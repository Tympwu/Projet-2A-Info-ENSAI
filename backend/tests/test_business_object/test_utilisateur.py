"""Tests unitaires pour le business object Utilisateur."""

import pytest
from business_object.utilisateur import Utilisateur
from business_object.historique import Historique


def test_utilisateur_init_complet():
    """Vérifie l'initialisation d'un utilisateur avec tous les arguments fournis."""
    historique = Historique(id=1, audits=[])
    user = Utilisateur(
        id=1,
        name="Alice",
        email="alice@test.com",
        mot_de_passe="secure_hash_123",
        historique=historique
    )

    assert user.id == 1
    assert user.name == "Alice"
    assert user.email == "alice@test.com"
    assert user.mot_de_passe == "secure_hash_123"
    assert user.historique == historique


def test_utilisateur_init_defaut():
    """Vérifie l'initialisation avec les valeurs par défaut (id et historique à None)."""
    user = Utilisateur(
        name="Bob",
        email="bob@test.com",
        mot_de_passe="password_abc"
    )

    assert user.id is None
    assert user.name == "Bob"
    assert user.email == "bob@test.com"
    assert user.mot_de_passe == "password_abc"
    assert user.historique is None


def test_utilisateur_repr():
    """Vérifie la méthode __repr__ de la classe Utilisateur."""
    user = Utilisateur(
        id=42,
        name="Charlie",
        email="charlie@test.com",
        mot_de_passe="secret"
    )

    representation_attendue = "Utilisateur(id=42, name='Charlie', email='charlie@test.com')"
    assert repr(user) == representation_attendue