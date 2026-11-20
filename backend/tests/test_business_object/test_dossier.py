
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
    """Vérifie l'initialisation avec tous les paramètres."""
    date_fixe = datetime(2026, 1, 1, 12, 0)

    dossier = Dossier(
        nom="MonDossier",
        liste_fichiers=[faux_fichier],
        signature_HMAC="abc123hmac",
        date_soumission=date_fixe,
    )

    assert dossier.nom == "MonDossier"
    assert dossier.liste_fichiers == [faux_fichier]
    assert dossier._Dossier__signature_HMAC == "abc123hmac"
    assert dossier.date_soumission == date_fixe


def test_dossier_init_defaut(faux_fichier):
    """Vérifie les valeurs par défaut de la signature et de la date."""
    dossier = Dossier(
        nom="MonDossier",
        liste_fichiers=[faux_fichier],
    )

    assert dossier.nom == "MonDossier"
    assert dossier._Dossier__signature_HMAC is None
    assert isinstance(dossier.date_soumission, datetime)


def test_obtenir_fichiers(faux_fichier):
    """Vérifie la récupération des fichiers du dossier."""
    dossier = Dossier(
        nom="Projet",
        liste_fichiers=[faux_fichier],
    )

    assert dossier.obtenir_fichiers() == [faux_fichier]


def test_obtenir_dependances_dossier():
    """Vérifie le regroupement des dépendances sans doublons."""
    dep1 = MagicMock(spec=Dependances)
    dep1.nom = "requests"
    dep1.version = "2.28.0"

    dep2 = MagicMock(spec=Dependances)
    dep2.nom = "pytest"
    dep2.version = "7.0.0"

    dep1_bis = MagicMock(spec=Dependances)
    dep1_bis.nom = "requests"
    dep1_bis.version = "2.28.0"

    f1 = MagicMock(spec=Fichier)
    f1.obtenir_dependances_fichier.return_value = [dep1, dep2]

    f2 = MagicMock(spec=Fichier)
    f2.obtenir_dependances_fichier.return_value = [dep1_bis]

    dossier = Dossier(
        nom="Projet",
        liste_fichiers=[f1, f2],
    )

    deps = dossier.obtenir_dependances_dossier()

    assert len(deps) == 2
    assert dep1 in deps
    assert dep2 in deps


def test_dossier_repr(faux_fichier):
    """Vérifie la représentation textuelle du dossier."""
    dossier = Dossier(
        nom="MonProjet",
        liste_fichiers=[faux_fichier, faux_fichier],
    )

    assert repr(dossier) == "Dossier('MonProjet', 2 fichier(s))"
