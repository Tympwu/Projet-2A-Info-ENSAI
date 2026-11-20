"""Tests unitaires de DossierService (DAO, analyse et utilisateur connecté simulés)."""

from unittest.mock import MagicMock, patch

import pytest

from business_object.audit import Audit
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from service.dossier_service import DossierService


@pytest.fixture
def faux_fichier_dao():
    """Remplace FichierDao."""
    with patch("service.dossier_service.FichierDao") as faux:
        yield faux.return_value


@pytest.fixture
def faux_audit_dao():
    """Remplace AuditDao : la création et l'enregistrement de l'audit réussissent par défaut."""
    with patch("service.dossier_service.AuditDao") as faux:
        faux.return_value.create_audit.return_value = True
        faux.return_value.update_audit.return_value = True
        yield faux.return_value


@pytest.fixture
def faux_analyse_fichier():
    """Remplace Analyse_fichier : l'analyse des dépendances donne un score de 2 à chaque fichier."""
    with patch("service.dossier_service.Analyse_fichier") as faux:
        analyse = faux.return_value
        analyse.detecter_anti_patterns.return_value = []

        def donner_un_score(fichier):
            fichier.score = 2.0
            return True

        analyse.analyse_dependances.side_effect = donner_un_score
        yield analyse


@pytest.fixture
def utilisateur_connecte():
    """Remplace UtilisateurService : par défaut, personne n'est connecté."""
    with patch("service.dossier_service.UtilisateurService") as faux:
        faux.return_value.utilisateur_connecte = None
        yield faux.return_value


@pytest.fixture
def service(faux_fichier_dao, faux_audit_dao, faux_analyse_fichier, utilisateur_connecte):
    """DossierService dont toutes les dépendances sont simulées."""
    return DossierService()


def un_dossier() -> Dossier:
    """Dossier réaliste : un requirements.txt et un fichier Python."""
    return Dossier(
        nom="projet",
        liste_fichiers=[
            Fichier(code="requests==2.31.0\n", extension=".txt"),
            Fichier(code="def f(l):\n    for x in l:\n        pass\n", extension=".py"),
        ],
    )


# --- Consultation et gestion des fichiers ---


def test_find_all_fichier(service, faux_fichier_dao):
    fichiers = [Fichier(code="a", id=1), Fichier(code="b", id=2)]
    faux_fichier_dao.find_all.return_value = fichiers

    assert service.find_all_fichier() == fichiers


def test_find_fichier_by_id(service, faux_fichier_dao):
    fichier = Fichier(code="a", id=5)
    faux_fichier_dao.find_fichier.return_value = fichier

    assert service.find_fichier_by_id(5) == fichier
    faux_fichier_dao.find_fichier.assert_called_once_with(5)


def test_find_fichier_by_user(service, faux_fichier_dao):
    faux_fichier_dao.find_by_utilisateur.return_value = []

    assert service.find_fichier_by_user(3) == []
    faux_fichier_dao.find_by_utilisateur.assert_called_once_with(3)


def test_find_fichier_by_user_inconnu(service, faux_fichier_dao):
    faux_fichier_dao.find_by_utilisateur.side_effect = ValueError("utilisateur inconnu")

    assert service.find_fichier_by_user(99) is None


def test_remove_fichier(service, faux_fichier_dao):
    faux_fichier_dao.remove_fichier.return_value = True

    assert service.remove_fichier(4) is True
    faux_fichier_dao.remove_fichier.assert_called_once_with(4)


def test_create_fichier_succes(service, faux_fichier_dao):
    fichier = Fichier(code="x = 1", extension=".py")
    faux_fichier_dao.create_fichier.return_value = True

    assert service.create_fichier(fichier) is fichier


def test_create_fichier_echec(service, faux_fichier_dao):
    faux_fichier_dao.create_fichier.return_value = False

    assert service.create_fichier(Fichier(code="x = 1", extension=".py")) is None


def test_update_fichier_succes(service, faux_fichier_dao):
    fichier = Fichier(code="x = 2", extension=".py", id=7)
    faux_fichier_dao.update_fichier.return_value = True
    faux_fichier_dao.find_fichier.return_value = fichier

    assert service.update_fichier(fichier, id_audit=3) is fichier
    faux_fichier_dao.update_fichier.assert_called_once_with(fichier=fichier, id_audit=3)


def test_update_fichier_echec(service, faux_fichier_dao):
    faux_fichier_dao.update_fichier.return_value = False

    assert service.update_fichier(Fichier(code="", id=7)) is None


def test_update_fichier_deja_traite(service, faux_fichier_dao):
    faux_fichier_dao.update_fichier.side_effect = ValueError("déjà traité")

    assert service.update_fichier(Fichier(code="", id=7)) is None


def test_consulter_dossier(service, faux_fichier_dao):
    dossier = Dossier(nom="", liste_fichiers=[])
    faux_fichier_dao.read_dossier.return_value = dossier

    assert service.consulter_dossier(8) is dossier
    faux_fichier_dao.read_dossier.assert_called_once_with(8)


# --- Émissions CO2 ---


def test_traiter_emission_dossier(service, faux_analyse_fichier):
    f1, f2 = Fichier(code="", extension=".py"), Fichier(code="", extension=".py")
    audit = Audit(dossier=Dossier(nom="", liste_fichiers=[f1, f2]))
    faux_analyse_fichier.estimer_emission_fichier.side_effect = [1.5, 2.5]

    resultat = service.traiter_emission_dossier(audit, n=100)

    assert resultat.emissionCO2_total == 4.0
    assert (f1.emissionCO2, f2.emissionCO2) == (1.5, 2.5)
    faux_analyse_fichier.estimer_emission_fichier.assert_any_call(f1, taille_reference=100)


def test_traiter_emission_dossier_ignore_les_fichiers_non_python(service, faux_analyse_fichier):
    """Régression : un requirements.txt n'a pas de complexité, il ne doit pas faire planter l'audit."""
    requirements = Fichier(code="requests==2.31.0\n", extension=".txt")
    script = Fichier(code="", extension=".py")
    audit = Audit(dossier=Dossier(nom="", liste_fichiers=[requirements, script]))
    faux_analyse_fichier.estimer_emission_fichier.return_value = 2.0

    resultat = service.traiter_emission_dossier(audit, n=100)

    assert resultat.emissionCO2_total == 2.0
    assert requirements.emissionCO2 is None
    faux_analyse_fichier.estimer_emission_fichier.assert_called_once_with(
        script, taille_reference=100
    )


# --- Traitement complet d'un dossier (audit) ---


def test_traiter_dossier_succes(service, faux_audit_dao):
    dossier = un_dossier()

    audit = service.traiter_dossier(dossier)

    assert isinstance(audit, Audit)
    assert audit.statut == "validé"  # score 2 < 5
    assert audit.score == 2.0
    assert dossier.liste_fichiers[1].liste_anti_pattern == []
    faux_audit_dao.create_audit.assert_called_once_with(audit, None)  # personne de connecté
    faux_audit_dao.update_audit.assert_called_once_with(audit)


def test_traiter_dossier_rattache_l_audit_a_l_utilisateur_connecte(
    service, faux_audit_dao, utilisateur_connecte
):
    utilisateur_connecte.utilisateur_connecte = MagicMock(id=42)

    audit = service.traiter_dossier(un_dossier())

    faux_audit_dao.create_audit.assert_called_once_with(audit, 42)


def test_traiter_dossier_anti_patterns_seulement_sur_les_py(service, faux_analyse_fichier):
    service.traiter_dossier(un_dossier())

    faux_analyse_fichier.detecter_anti_patterns.assert_called_once()


def test_traiter_dossier_echec_creation_audit(service, faux_audit_dao):
    faux_audit_dao.create_audit.return_value = False

    assert service.traiter_dossier(un_dossier()) is None


def test_traiter_dossier_fichier_illisible(service):
    dossier = Dossier(nom="projet", liste_fichiers=[Fichier(code="", extension=".js")])

    with pytest.raises(FileNotFoundError):
        service.traiter_dossier(dossier)


def test_traiter_dossier_echec_anti_patterns(service, faux_analyse_fichier):
    faux_analyse_fichier.detecter_anti_patterns.return_value = None

    with pytest.raises(ValueError):
        service.traiter_dossier(un_dossier())


def test_traiter_dossier_echec_analyse_dependances(service, faux_analyse_fichier):
    faux_analyse_fichier.analyse_dependances.side_effect = None
    faux_analyse_fichier.analyse_dependances.return_value = False

    with pytest.raises(ArithmeticError):
        service.traiter_dossier(un_dossier())


def test_traiter_dossier_dossier_vide(service):
    """Un dossier sans fichier ne peut pas avoir de score : l'audit échoue."""
    with pytest.raises(ArithmeticError):
        service.traiter_dossier(Dossier(nom="vide", liste_fichiers=[]))


def test_traiter_dossier_echec_enregistrement(service, faux_audit_dao):
    faux_audit_dao.update_audit.return_value = False

    with pytest.raises(ValueError):
        service.traiter_dossier(un_dossier())
