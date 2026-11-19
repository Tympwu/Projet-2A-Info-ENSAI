"""Tests unitaires de DossierService."""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from service.dossier_service import DossierService
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from business_object.audit import Audit


@pytest.fixture
def faux_fichier_dao():
    """Remplace FichierDao."""
    with patch("service.dossier_service.FichierDao") as faux:
        yield faux.return_value


@pytest.fixture
def faux_audit_dao():
    """Remplace AuditDao."""
    with patch("service.dossier_service.AuditDao") as faux:
        yield faux.return_value


@pytest.fixture
def faux_analyse_fichier():
    """Remplace Analyse_fichier."""
    with patch("service.dossier_service.Analyse_fichier") as faux:
        yield faux.return_value


@pytest.fixture
def service(faux_fichier_dao, faux_audit_dao, faux_analyse_fichier):
    """Retourne une instance de DossierService avec ses dépendances mockées."""
    return DossierService()


# --- Tests de consultation et gestion des fichiers ---

def test_find_all_fichier(service, faux_fichier_dao):
    """Vérifie la récupération de tous les fichiers."""
    fichiers_attendus = [Fichier(id=1), Fichier(id=2)]
    faux_fichier_dao.find_all.return_value = fichiers_attendus

    resultat = service.find_all_fichier()

    assert resultat == fichiers_attendus
    faux_fichier_dao.find_all.assert_called_once()


def test_find_fichier_by_id(service, faux_fichier_dao):
    """Vérifie la recherche d'un fichier par son ID."""
    fichier_attendu = Fichier(id=5)
    faux_fichier_dao.find_fichier.return_value = fichier_attendu

    resultat = service.find_fichier_by_id(5)

    assert resultat == fichier_attendu
    faux_fichier_dao.find_fichier.assert_called_once_with(5)


def test_create_dossier_succes(service, faux_fichier_dao):
    """Vérifie la création d'un dossier (tous les fichiers réussissent)."""
    faux_fichier_dao.create_fichier.return_value = True
    fichiers = [Fichier(chemin="a.py"), Fichier(chemin="b.py")]

    assert service.create_dossier(fichiers) is True
    assert faux_fichier_dao.create_fichier.call_count == 2


def test_create_dossier_echec_partiel(service, faux_fichier_dao):
    """Vérifie qu'un échec de création sur un fichier retourne False."""
    faux_fichier_dao.create_fichier.side_effect = [True, False]
    fichiers = [Fichier(chemin="a.py"), Fichier(chemin="b.py")]

    assert service.create_dossier(fichiers) is False


def test_remove_dossier(service, faux_fichier_dao):
    """Vérifie la suppression d'un dossier."""
    faux_fichier_dao.remove_dossier.return_value = True

    assert service.remove_dossier("/path/to/dir") is True
    faux_fichier_dao.remove_dossier.assert_called_once_with("/path/to/dir")


def test_update_dossier_succes(service, faux_fichier_dao):
    """Vérifie la mise à jour d'un dossier existant."""
    dossier_init = Dossier(nom="ancien")
    nouveau_dossier = Dossier(nom="nouveau")
    faux_fichier_dao.read_dossier.return_value = dossier_init
    faux_fichier_dao.update_dossier.return_value = True

    resultat = service.update_dossier("/path", nouveau_dossier)

    assert resultat is True
    faux_fichier_dao.update_dossier.assert_called_once_with(dossier_init, dossier_nouv=nouveau_dossier)


def test_update_dossier_inexistant_leve_erreur(service, faux_fichier_dao):
    """Vérifie qu'une ValueError est levée si le dossier à mettre à jour n'existe pas."""
    faux_fichier_dao.read_dossier.return_value = None

    with pytest.raises(ValueError, match="L'adresse fourni du premier dossier n'est pas valide"):
        service.update_dossier("/path", Dossier(nom="nouveau"))


def test_consulter_dossier(service, faux_fichier_dao):
    """Vérifie la consultation d'un dossier par son chemin."""
    dossier_attendu = Dossier(nom="test")
    faux_fichier_dao.read_dossier.return_value = dossier_attendu

    assert service.consulter_dossier("/path") == dossier_attendu
    faux_fichier_dao.read_dossier.assert_called_once_with("/path")


# --- Tests de l'analyse d'émissions CO2 ---

def test_traiter_emission_dossier(service, faux_analyse_fichier):
    """Vérifie le calcul et l'accumulation des émissions CO2 pour les fichiers du dossier."""
    f1 = MagicMock(emissionCO2=None)
    f2 = MagicMock(emissionCO2=None)
    dossier = MagicMock(liste_fichiers=[f1, f2])
    audit = Audit(dossier=dossier)

    faux_analyse_fichier.calculer_emissionCO2e.side_effect = [1.5, 2.5]

    resultat = service.traiter_emission_dossier(audit, n=100)

    assert resultat.emissionCO2_total == 4.0
    assert f1.emissionCO2 == 1.5
    assert f2.emissionCO2 == 2.5
    assert faux_analyse_fichier.calculer_emissionCO2e.call_count == 2


# --- Tests de l'analyse et traitement global d'un dossier ---

def test_traiter_dossier_succes(service, faux_audit_dao, faux_analyse_fichier):
    """Vérifie le traitement complet et réussi d'un dossier pour un audit."""
    fichiers = [MagicMock(spec=Fichier)]
    fichiers[0].extraire_dependances.return_value = True
    
    dossier = Dossier(nom="test", liste_fichiers=fichiers)
    faux_audit_dao.create_audit.return_value = True
    
    faux_analyse_fichier.detecter_anti_patterns.return_value = ["pattern1"]
    faux_analyse_fichier.analyse_dependances.return_value = True

    audit_obtenu = service.traiter_dossier(dossier, id_utilisateur=1)

    assert audit_obtenu is not None
    assert isinstance(audit_obtenu, Audit)
    faux_audit_dao.create_audit.assert_called_once()
    assert fichiers[0].liste_anti_pattern == ["pattern1"]


def test_traiter_dossier_echec_creation_audit(service, faux_audit_dao):
    """Vérifie que traiter_dossier retourne None si la création de l'audit en base échoue."""
    faux_audit_dao.create_audit.return_value = False
    dossier = Dossier(nom="test", liste_fichiers=[])

    assert service.traiter_dossier(dossier) is None


def test_traiter_dossier_echec_dependance_fichier(service, faux_audit_dao):
    """Vérifie que le traitement s'arrête et retourne None si l'extraction des dépendances échoue."""
    fichier = MagicMock(spec=Fichier)
    fichier.extraire_dependances.return_value = False
    dossier = Dossier(nom="test", liste_fichiers=[fichier])
    faux_audit_dao.create_audit.return_value = True

    assert service.traiter_dossier(dossier) is None


def test_traiter_dossier_fichier_introuvable(service, faux_audit_dao):
    """Vérifie la gestion de l'exception FileNotFoundError lors du traitement d'un fichier."""
    fichier = MagicMock(spec=Fichier)
    fichier.extraire_dependances.side_effect = FileNotFoundError()
    dossier = Dossier(nom="test", liste_fichiers=[fichier])
    faux_audit_dao.create_audit.return_value = True

    assert service.traiter_dossier(dossier) is None
