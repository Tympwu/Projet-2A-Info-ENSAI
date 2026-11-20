"""Tests unitaires de UtilisateurService."""

from unittest.mock import patch

import pytest

from business_object.historique import Historique
from business_object.utilisateur import Utilisateur
from service.utilisateur_service import UtilisateurService
from utils.security import hash_mdp
from utils.singleton import Singleton


@pytest.fixture
def faux_utilisateur_dao():
    """Remplace UtilisateurDao : aucun accès à la base de données."""
    with patch("service.utilisateur_service.UtilisateurDao") as faux:
        yield faux.return_value


@pytest.fixture
def service(faux_utilisateur_dao):
    """Nouvelle instance de UtilisateurService, avec son DAO simulé.

    UtilisateurService est un singleton : sans précaution, tous les tests
    recevraient la même instance, créée au premier test avec son DAO
    (éventuellement le vrai, ce qui tente de se connecter à la base).
    On retire donc l'instance mémorisée avant et après chaque test.
    """
    Singleton._instances.pop(UtilisateurService, None)
    yield UtilisateurService()
    Singleton._instances.pop(UtilisateurService, None)


def un_utilisateur(id=1, name="alice") -> Utilisateur:
    return Utilisateur(id=id, name=name, email=f"{name}@test.com", mot_de_passe="hash")


# --- Création ---


def test_create_utilisateur_succes(service, faux_utilisateur_dao):
    """Le mot de passe est haché avant d'être envoyé au DAO, et un historique vide est créé."""
    faux_utilisateur_dao.create_utilisateur.return_value = True

    resultat = service.create_utilisateur("alice", "secret123", "alice@test.com")

    assert resultat.name == "alice"
    assert resultat.email == "alice@test.com"
    assert resultat.mot_de_passe == hash_mdp("secret123", "alice")
    assert resultat.mot_de_passe != "secret123"
    assert isinstance(resultat.historique, Historique)


def test_create_utilisateur_echec(service, faux_utilisateur_dao):
    faux_utilisateur_dao.create_utilisateur.return_value = False

    assert service.create_utilisateur("alice", "secret123", "alice@test.com") is None


# --- Mise à jour ---


def test_update_utilisateur_succes(service, faux_utilisateur_dao):
    utilisateur = un_utilisateur(name="ancien")
    faux_utilisateur_dao.find_utilisateur.return_value = utilisateur
    faux_utilisateur_dao.update_utilisateur.return_value = True

    resultat = service.update_utilisateur(1, "nouveau", "newmdp", "nouveau@test.com")

    assert resultat is utilisateur
    assert utilisateur.name == "nouveau"
    assert utilisateur.email == "nouveau@test.com"
    # Même hachage qu'à la création : l'utilisateur pourra se reconnecter.
    assert utilisateur.mot_de_passe == hash_mdp("newmdp", "nouveau")


def test_update_utilisateur_inexistant(service, faux_utilisateur_dao):
    faux_utilisateur_dao.find_utilisateur.return_value = None

    assert service.update_utilisateur(99, "nom", "mdp", "email@test.com") is False
    faux_utilisateur_dao.update_utilisateur.assert_not_called()


def test_update_utilisateur_echec_dao(service, faux_utilisateur_dao):
    faux_utilisateur_dao.find_utilisateur.return_value = un_utilisateur()
    faux_utilisateur_dao.update_utilisateur.return_value = False

    assert service.update_utilisateur(1, "alice", "mdp", "alice@test.com") is None


# --- Suppression ---


def test_remove_utilisateur_succes(service, faux_utilisateur_dao):
    utilisateur = un_utilisateur()
    faux_utilisateur_dao.find_utilisateur.return_value = utilisateur
    faux_utilisateur_dao.remove_utilisateur.return_value = True

    assert service.remove_utilisateur(1) is True
    faux_utilisateur_dao.remove_utilisateur.assert_called_once_with(utilisateur)


def test_remove_utilisateur_inexistant(service, faux_utilisateur_dao):
    faux_utilisateur_dao.find_utilisateur.return_value = None

    assert service.remove_utilisateur(99) is False
    faux_utilisateur_dao.remove_utilisateur.assert_not_called()


# --- Recherche ---


def test_find_utilisateur(service, faux_utilisateur_dao):
    utilisateur = un_utilisateur()
    faux_utilisateur_dao.find_utilisateur.return_value = utilisateur

    assert service.find_utilisateur(1) is utilisateur
    faux_utilisateur_dao.find_utilisateur.assert_called_once_with(1)


def test_find_utilisateur_by_name(service, faux_utilisateur_dao):
    utilisateurs = [un_utilisateur()]
    faux_utilisateur_dao.find_utilisateur_by_name.return_value = utilisateurs

    assert service.find_utilisateur_by_name("alice") == utilisateurs
    faux_utilisateur_dao.find_utilisateur_by_name.assert_called_once_with("alice")


def test_find_all_utilisateurs(service, faux_utilisateur_dao):
    utilisateurs = [un_utilisateur(1, "alice"), un_utilisateur(2, "bob")]
    faux_utilisateur_dao.find_all.return_value = utilisateurs

    assert service.find_all_utilisateurs() == utilisateurs


# --- Connexion ---


def test_login_succes(service, faux_utilisateur_dao):
    """Le DAO reçoit le mot de passe haché, et l'utilisateur devient l'utilisateur connecté."""
    utilisateur = un_utilisateur()
    faux_utilisateur_dao.login_utilisateur.return_value = utilisateur

    resultat = service.login("alice", "secret123")

    assert resultat is utilisateur
    assert service.utilisateur_connecte is utilisateur
    faux_utilisateur_dao.login_utilisateur.assert_called_once_with(
        nom="alice", mot_de_passe=hash_mdp("secret123", "alice")
    )


def test_login_echec(service, faux_utilisateur_dao):
    """Un échec de connexion remet l'utilisateur connecté à None."""
    faux_utilisateur_dao.login_utilisateur.return_value = None
    service.utilisateur_connecte = un_utilisateur(name="ancien")

    assert service.login("alice", "mauvais_mdp") is None
    assert service.utilisateur_connecte is None


def test_hachage_identique_a_la_creation_et_a_la_connexion(service, faux_utilisateur_dao):
    """Régression : la création et la connexion doivent hacher le mot de passe de la même façon."""
    faux_utilisateur_dao.create_utilisateur.return_value = True
    cree = service.create_utilisateur("alice", "secret123", "alice@test.com")

    service.login("alice", "secret123")

    mot_de_passe_envoye = faux_utilisateur_dao.login_utilisateur.call_args.kwargs["mot_de_passe"]
    assert mot_de_passe_envoye == cree.mot_de_passe
