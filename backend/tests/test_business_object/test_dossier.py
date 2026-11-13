"""Tests unitaires pour le business object Dossier."""

from datetime import datetime
from unittest.mock import MagicMock
import pytest

from business_object.dossier import Dossier
from business_object.fichier import Fichier
from business_object.dependance import Dependances


@pytest.fixture
def faux_fichier():
    """Crée un faux fichier pour les tests."""
    return MagicMock(spec=Fichier)


def test_dossier_init_complet(faux_fichier):
    """Vérifie l'initialisation d'un dossier avec tous les paramètres."""
    date_fixe = datetime(2026, 1, 1, 12, 0)
    dossier = Dossier(
        nom="MonDossier",
        chemin="/path/to/dossier",
        liste_fichiers=[faux_fichier],
        signature_HMAC="abc123hmac",
        date_soumission=date_fixe,
    )

    assert dossier.nom == "MonDossier"
    assert dossier.chemin == "/path/to/dossier"
    assert dossier.liste_fichiers == [faux_fichier]
    assert dossier._signature_HMAC == "abc123hmac"
    assert dossier.date_soumission == date_fixe


def test_dossier_init_defaut(faux_fichier):
    """Vérifie l'initialisation avec les valeurs par défaut (HMAC et date)."""
    dossier = Dossier(
        nom="MonDossier",
        chemin="/path/to/dossier",
        liste_fichiers=[faux_fichier],
    )

    assert dossier.nom == "MonDossier"
    assert dossier._signature_HMAC is None
    assert isinstance(dossier.date_soumission, datetime)


def test_obtenir_fichiers(faux_fichier):
    """Vérifie la récupération de la liste des fichiers."""
    dossier = Dossier(
        nom="Projet",
        chemin="/tmp",
        liste_fichiers=[faux_fichier],
    )

    assert dossier.obtenir_fichiers() == [faux_fichier]


def test_obtenir_dependances_dossier():
    """Vérifie le regroupement des dépendances sans doublons."""
    # Création de dépendances fictives
    dep1 = MagicMock(spec=Dependances)
    dep1.nom = "requests"
    dep1.version = "2.28.0"

    dep2 = MagicMock(spec=Dependances)
    dep2.nom = "pytest"
    dep2.version = "7.0.0"

    dep1_bis = MagicMock(spec=Dependances)
    dep1_bis.nom = "requests"
    dep1_bis.version = "2.28.0"  # Doublon exact (nom + version)

    # Fichiers mockés retournant des listes de dépendances
    f1 = MagicMock(spec=Fichier)
    f1.obtenir_dependances_fichier.return_value = [dep1, dep2]

    f2 = MagicMock(spec=Fichier)
    f2.obtenir_dependances_fichier.return_value = [dep1_bis]  # Doit être filtré

    dossier = Dossier(
        nom="Projet",
        chemin="/tmp",
        liste_fichiers=[f1, f2],
    )

    deps = dossier.obtenir_dependances_dossier()

    # On doit retrouver uniquement dep1 et dep2 (pas de doublon de dep1_bis)
    assert len(deps) == 2
    assert dep1 in deps
    assert dep2 in deps


def test_dossier_repr(faux_fichier):
    """Vérifie la représentation textuelle de la classe Dossier."""
    dossier = Dossier(
        nom="MonProjet",
        chemin="/tmp",
        liste_fichiers=[faux_fichier, faux_fichier],
    )

    assert repr(dossier) == "Dossier('MonProjet', 2 fichier"