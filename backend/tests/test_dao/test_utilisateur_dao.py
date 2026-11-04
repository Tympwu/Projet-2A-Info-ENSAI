"""Tests unitaires de UtilisateurDao."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dao.utilisateur_dao import UtilisateurDao


@pytest.fixture
def curseur():
    """Remplace la connexion à la base par un faux curseur."""
    with patch("dao.utilisateur_dao.DBConnection") as faux_db:
        connexion = faux_db.return_value.connection.__enter__.return_value
        yield connexion.cursor.return_value.__enter__.return_value


@pytest.fixture
def faux_audit_dao():
    """Remplace AuditDao pour éviter les appels réels lors de l'instanciation de l'Historique."""
    with patch("dao.utilisateur_dao.AuditDao") as faux:
        faux.return_value.find_by_utilisateur.return_value = []
        yield faux.return_value


@pytest.fixture
def dao():
    """Retourne le DAO testé (c'est un singleton)."""
    return UtilisateurDao()


@pytest.fixture
def utilisateur():
    """Retourne un utilisateur minimal avec les attributs que le DAO lit."""
    return SimpleNamespace(
        id=1,
        name="Alice",
        email="alice@example.com",
        mot_de_passe="hashed_mdp_123",
    )


def ligne(id_user=1):
    """Retourne une ligne telle que la base la renverrait pour un utilisateur."""
    return {
        "id": id_user,
        "name": "Alice",
        "email": "alice@example.com",
        "mot_de_passe": "hashed_mdp_123",
    }


def test_create_utilisateur_succes(dao, curseur, utilisateur):
    curseur.fetchone.return_value = {"id": 10}

    assert dao.create_utilisateur(utilisateur) is True

    assert utilisateur.id == 10  # L'ID généré par la base est récupéré
    parametres = curseur.execute.call_args.args[1]
    assert parametres["name"] == "Alice"
    assert parametres["email"] == "alice@example.com"
    assert parametres["mot_de_passe"] == "hashed_mdp_123"


def test_create_utilisateur_sans_resultat(dao, curseur, utilisateur):
    curseur.fetchone.return_value = None

    assert dao.create_utilisateur(utilisateur) is False
    assert utilisateur.id == 1  # Inchangé


def test_update_utilisateur_succes(dao, curseur, utilisateur):
    curseur.rowcount = 1

    assert dao.update_utilisateur(utilisateur) is True
    assert curseur.execute.call_args.args[1]["id_utilisateur"] == 1


def test_update_utilisateur_introuvable(dao, curseur, utilisateur):
    curseur.rowcount = 0

    assert dao.update_utilisateur(utilisateur) is False


def test_remove_utilisateur_succes(dao, curseur, utilisateur):
    curseur.rowcount = 1

    assert dao.remove_utilisateur(utilisateur) is True
    assert curseur.execute.call_args.args[1] == {"id_utilisateur": 1}


def test_remove_utilisateur_introuvable(dao, curseur, utilisateur):
    curseur.rowcount = 0

    assert dao.remove_utilisateur(utilisateur) is False


def test_find_utilisateur_trouve(dao, curseur, faux_audit_dao):
    curseur.fetchone.return_value = ligne(2)

    u = dao.find_utilisateur(2)

    assert u is not None
    assert u.id == 2
    assert u.name == "Alice"
    assert u.email == "alice@example.com"
    assert u.mot_de_passe == "hashed_mdp_123"
    assert u.historique is not None
    faux_audit_dao.find_by_utilisateur.assert_called_once_with(2)


def test_find_utilisateur_introuvable(dao, curseur, faux_audit_dao):
    curseur.fetchone.return_value = None

    assert dao.find_utilisateur(99) is None
    faux_audit_dao.find_by_utilisateur.assert_not_called()


def test_find_utilisateur_by_name(dao, curseur, faux_audit_dao):
    curseur.fetchall.return_value = [ligne(1)]

    utilisateurs = dao.find_utilisateur_by_name("Alice")

    assert len(utilisateurs) == 1
    assert utilisateurs[0].name == "Alice"
    assert curseur.execute.call_args.args[1] == {"name_user": "Alice"}
    faux_audit_dao.find_by_utilisateur.assert_called_once_with(1)


def test_find_all(dao, curseur, faux_audit_dao):
    curseur.fetchall.return_value = [ligne(1), ligne(2)]

    utilisateurs = dao.find_all()

    assert len(utilisateurs) == 2
    assert utilisateurs[0].id == 1
    assert utilisateurs[1].id == 2
    assert faux_audit_dao.find_by_utilisateur.call_count == 2


def test_login_utilisateur_succes(dao, curseur, faux_audit_dao):
    curseur.fetchone.return_value = ligne(1)

    u = dao.login_utilisateur("Alice", "hashed_mdp_123")

    assert u is not None
    assert u.name == "Alice"
    assert curseur.execute.call_args.args[1] == {
        "name": "Alice",
        "mot_de_passe": "hashed_mdp_123",
    }
    faux_audit_dao.find_by_utilisateur.assert_called_once_with(1)


def test_login_utilisateur_echec(dao, curseur, faux_audit_dao):
    curseur.fetchone.return_value = None

    u = dao.login_utilisateur("Alice", "mauvais_mdp")

    assert u is None
    faux_audit_dao.find_by_utilisateur.assert_not_called()


@pytest.mark.parametrize(
    "appel",
    [
        lambda dao, utilisateur: dao.create_utilisateur(utilisateur),
        lambda dao, utilisateur: dao.update_utilisateur(utilisateur),
        lambda dao, utilisateur: dao.remove_utilisateur(utilisateur),
        lambda dao, utilisateur: dao.find_utilisateur(1),
        lambda dao, utilisateur: dao.find_utilisateur_by_name("Alice"),
        lambda dao, utilisateur: dao.find_all(),
        lambda dao, utilisateur: dao.login_utilisateur("Alice", "mdp"),
    ],
    ids=[
        "create",
        "update",
        "remove",
        "find",
        "find_by_name",
        "find_all",
        "login",
    ],
)
def test_erreur_bd_remontee(dao, curseur, utilisateur, appel):
    """Une erreur de la base n'est pas avalée : elle remonte à l'appelant."""
    curseur.execute.side_effect = RuntimeError("base indisponible")

    with pytest.raises(RuntimeError):
        appel(dao, utilisateur)