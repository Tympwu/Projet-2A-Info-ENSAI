"""Tests unitaires de Fichier_service."""

from unittest.mock import MagicMock, patch
import pytest

from service.fichier_service import Fichier_service
from business_object.fichier import Fichier


@pytest.fixture
def faux_fichier_dao():
    """Remplace FichierDao pour isoler les tests de la couche service."""
    # Note : adapte le chemin d'import du patch si ton fichier service est dans un package spécifique
    with patch("service.fichier_service.FichierDao") as faux:
        yield faux.return_value


@pytest.fixture
def service(faux_fichier_dao):
    """Retourne une instance de Fichier_service avec un DAO mocké."""
    return Fichier_service()


def test_find_fichier_by_id_trouve(service, faux_fichier_dao):
    """Vérifie que le service appelle correctement le DAO et retourne le fichier."""
    fichier_attendu = Fichier(id=5, chemin="/test/main.py", extension="py", complexite=2, score=95.0, emissionCO2=0.1)
    faux_fichier_dao.find_fichier.return_value = fichier_attendu

    resultat = service.find_fichier_by_id(5)

    assert resultat == fichier_attendu
    faux_fichier_dao.find_fichier.assert_called_once_with(5)


def test_find_fichier_by_id_introuvable(service, faux_fichier_dao):
    """Vérifie le comportement si le fichier n'existe pas."""
    faux_fichier_dao.find_fichier.return_value = None

    resultat = service.find_fichier_by_id(99)

    assert resultat is None
    faux_fichier_dao.find_fichier.assert_called_once_with(99)


def test_create_dossier_tous_succes(service, faux_fichier_dao):
    """Vérifie que la création de plusieurs fichiers retourne True si tout réussit."""
    faux_fichier_dao.create_fichier.return_value = True


    fichiers = [
        Fichier(chemin="/test/file1.py", extension="py"),
        Fichier(chemin="/test/file2.py", extension="py")
    ]

    success = service.create_dossier(fichiers, audit_id=10)

    assert success is True
    assert faux_fichier_dao.create_fichier.call_count == 2


def test_create_dossier_avec_echec_partiel(service, faux_fichier_dao):
    """Vérifie que la méthode retourne False si au moins un fichier échoue à la création."""
    faux_fichier_dao.create_fichier.side_effect = [True, False]

    fichiers = [
        Fichier(chemin="/test/file1.py", extension="py"),
        Fichier(chemin="/test/file2.py", extension="py")
    ]

    success = service.create_dossier(fichiers, audit_id=10)

    assert success is False
    assert faux_fichier_dao.create_fichier.call_count == 2