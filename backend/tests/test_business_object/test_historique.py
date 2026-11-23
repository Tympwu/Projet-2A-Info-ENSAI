"""Tests unitaires pour le business object Historique."""

from unittest.mock import MagicMock

import pytest

from business_object.audit import Audit
from business_object.historique import Historique


@pytest.fixture
def audit_1():
    """Crée un faux audit pour les tests."""
    a = MagicMock(spec=Audit)
    a.id = 1
    return a


@pytest.fixture
def audit_2():
    """Crée un second faux audit pour les tests."""
    a = MagicMock(spec=Audit)
    a.id = 2
    return a


def test_historique_init_avec_audits(audit_1):
    """Vérifie l'initialisation de l'historique avec une liste d'audits."""
    historique = Historique(id=10, audits=[audit_1])

    assert historique.id == 10
    assert historique.audits == [audit_1]


def test_historique_init_sans_audits():
    """Vérifie que la liste d'audits est bien initialisée à vide si on passe None."""
    historique = Historique(id=10, audits=None)

    assert historique.id == 10
    assert historique.audits == []


def test_consulter_historique(audit_1, audit_2):
    """Vérifie la récupération de tous les audits de l'historique."""
    historique = Historique(id=1, audits=[audit_1, audit_2])

    resultat = historique.consulter_historique()

    assert resultat == [audit_1, audit_2]


def test_ajout_historique(audit_1):
    """Vérifie l'ajout d'un nouvel audit dans l'historique."""
    historique = Historique(id=1, audits=[])

    assert len(historique.audits) == 0

    historique.ajout_historique(audit_1)

    assert len(historique.audits) == 1
    assert historique.audits[0] == audit_1


def test_consulter_audit_trouve(audit_1, audit_2):
    """Vérifie la recherche d'un audit existant par son identifiant."""
    historique = Historique(id=1, audits=[audit_1, audit_2])

    audit_trouve = historique.consulter_audit(2)

    assert audit_trouve == audit_2


def test_consulter_audit_non_trouve(audit_1):
    """Vérifie que la recherche d'un ID inexistant retourne None."""
    historique = Historique(id=1, audits=[audit_1])

    audit_trouve = historique.consulter_audit(99)

    assert audit_trouve is None
