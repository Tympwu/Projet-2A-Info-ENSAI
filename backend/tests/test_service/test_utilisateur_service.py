"""Tests unitaires de UtilisateurService."""

from unittest.mock import MagicMock, patch
import pytest

from service.utilisateur_service import UtilisateurService
from business_object.utilisateur import Utilisateur
from business_object.historique import Historique


@pytest.fixture
def faux_utilisateur_dao():
    """Remplace UtilisateurDao."""
    with patch("service.utilisateur_service.UtilisateurDao") as faux:
        yield faux.return_value


@pytest.fixture
def service(faux_utilisateur_dao):
    """Retourne une instance de UtilisateurService avec son DAO mocké."""
    return UtilisateurService()


def test_verif_hash_mdp(service):
    """Vérifie le hachage SHA-256 du mot de passe avec le nom comme sel."""
    mdp = "secret123"
    name = "alice"
    hash_result = service.verif_hash_mdp(mdp, name)
    
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64  # Longueur standard d'un hash SHA-256 en hexadécimal


def test_connexion_succes(service, faux_utilisateur_dao):
    """Vérifie la connexion d'un utilisateur avec des identifiants corrects."""
    user = Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="fake_hash")
    faux_utilisateur_dao.login_utilisateur.return_value = user

    resultat = service.connexion("alice", "secret123")

    assert resultat == user
    faux_utilisateur_dao.login_utilisateur.assert_called_once()


def test_create_utilisateur_succes(service, faux_utilisateur_dao):
    """Vérifie la création réussie d'un nouvel utilisateur et l'initialisation de son historique."""
    faux_utilisateur_dao.create_utilisateur.return_value = True

    resultat = service.create_utilisateur("alice", "secret123", "alice@test.com")

    assert resultat is not None
    assert resultat.name == "alice"
    assert resultat.email == "alice@test.com"
    assert isinstance(resultat.historique, Historique)
    faux_utilisateur_dao.create_utilisateur.assert_called_once()


def test_create_utilisateur_echec(service, faux_utilisateur_dao):
    """Vérifie que la création retourne None si le DAO échoue."""
    faux_utilisateur_dao.create_utilisateur.return_value = False

    resultat = service.create_utilisateur("alice", "secret123", "alice@test.com")

    assert resultat is None


def test_update_utilisateur_succes(service, faux_utilisateur_dao):
    """Vérifie la mise à jour des informations d'un utilisateur existant."""
    user = Utilisateur(id=1, name="ancien", email="ancien@test.com", mot_de_passe="old_hash")
    faux_utilisateur_dao.find_utilisateur.return_value = user
    faux_utilisateur_dao.update_utilisateur.return_value = True

    resultat = service.update_utilisateur(1, "nouveau", "newmdp", "nouveau@test.com")

    assert resultat == user
    assert user.name == "nouveau"
    assert user.email == "nouveau@test.com"
    faux_utilisateur_dao.update_utilisateur.assert_called_once()


def test_update_utilisateur_inexistant(service, faux_utilisateur_dao):
    """Vérifie que la mise à jour retourne False si l'utilisateur n'existe pas en base."""
    faux_utilisateur_dao.find_utilisateur.return_value = None

    resultat = service.update_utilisateur(99, "nom", "mdp", "email@test.com")

    assert resultat is False
    faux_utilisateur_dao.update_utilisateur.assert_not_called()


def test_remove_utilisateur_succes(service, faux_utilisateur_dao):
    """Vérifie la suppression d'un utilisateur existant."""
    user = Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="fake_hash")
    faux_utilisateur_dao.find_utilisateur.return_value = user
    faux_utilisateur_dao.remove_utilisateur.return_value = True

    resultat = service.remove_utilisateur(1)

    assert resultat is True
    faux_utilisateur_dao.remove_utilisateur.assert_called_once_with(user)


def test_remove_utilisateur_inexistant(service, faux_utilisateur_dao):
    """Vérifie que la suppression retourne False si l'utilisateur est introuvable."""
    faux_utilisateur_dao.find_utilisateur.return_value = None

    resultat = service.remove_utilisateur(99)

    assert resultat is False
    faux_utilisateur_dao.remove_utilisateur.assert_not_called()


def test_find_utilisateur(service, faux_utilisateur_dao):
    """Vérifie la recherche d'un utilisateur par son ID."""
    user = Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="fake_hash")
    faux_utilisateur_dao.find_utilisateur.return_value = user

    assert service.find_utilisateur(1) == user
    faux_utilisateur_dao.find_utilisateur.assert_called_once_with(1)


def test_find_utilisateur_by_name(service, faux_utilisateur_dao):
    """Vérifie la recherche d'utilisateurs par leur nom."""
    users = [Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="fake_hash")]
    faux_utilisateur_dao.find_utilisateur_by_name.return_value = users

    assert service.find_utilisateur_by_name("alice") == users
    faux_utilisateur_dao.find_utilisateur_by_name.assert_called_once_with("alice")


def test_find_all_utilisateurs(service, faux_utilisateur_dao):
    """Vérifie la récupération de tous les utilisateurs enregistrés."""
    users = [
        Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="hash1"),
        Utilisateur(id=2, name="bob", email="bob@test.com", mot_de_passe="hash2")
    ]
    faux_utilisateur_dao.find_all.return_value = users

    assert service.find_all_utilisateurs() == users
    faux_utilisateur_dao.find_all.assert_called_once()


def test_login_succes(service, faux_utilisateur_dao):
    """Vérifie la méthode de connexion principale et l'assignation de l'utilisateur connecté."""
    user = Utilisateur(id=1, name="alice", email="alice@test.com", mot_de_passe="fake_hash")
    faux_utilisateur_dao.login_utilisateur.return_value = user

    resultat = service.login("alice", "secret123")

    assert resultat == user
    assert service.utilisateur_connecte == user


def test_login_echec(service, faux_utilisateur_dao):
    """Vérifie qu'un échec de connexion remet l'utilisateur connecté à None."""
    faux_utilisateur_dao.login_utilisateur.return_value = None
    service.utilisateur_connecte = Utilisateur(id=1, name="ancien", email="ancien@test.com", mot_de_passe="old")

    resultat = service.login("alice", "mauvais_mdp")

    assert resultat is None
    assert service.utilisateur_connecte is None