"""Tests unitaires de FichierDao."""

import re
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dao.fichier_dao import FichierDao


@pytest.fixture
def curseur():
    """Remplace la connexion à la base par un faux curseur."""
    with patch("dao.fichier_dao.DBConnection") as faux_db:
        connexion = faux_db.return_value.connection.__enter__.return_value
        yield connexion.cursor.return_value.__enter__.return_value


@pytest.fixture
def dao():
    """Retourne le DAO testé (c'est un singleton)."""
    return FichierDao()


@pytest.fixture
def fichier():
    """Retourne un fichier minimal avec les attributs que le DAO lit."""
    return SimpleNamespace(
        id=1,
        chemin="/path/to/file.py",
        extension="py",
        complexite=5,
        score=90.0,
        emissionCO2=0.5,
    )


def ligne(id_fichier=1):
    """Retourne une ligne telle que la base la renverrait pour un fichier."""
    return {
        "id": id_fichier,
        "chemin": "/path/to/file.py",
        "extension": "py",
        "complexite": 5,
        "score": 90.0,
        "emissionco2": 0.5,
    }


def test_create_fichier_succes(dao, curseur, fichier):
    curseur.fetchone.return_value = {"id": 12}

    assert dao.create_fichier(fichier, audit_id=5) is True

    assert fichier.id == 12  # l'identifiant généré par la base est récupéré
    parametres = curseur.execute.call_args.args[1]
    assert parametres["audit_id"] == 5
    assert parametres["chemin"] == "/path/to/file.py"
    assert parametres["extension"] == "py"
    assert parametres["emissionco2"] == 0.5


def test_create_fichier_sans_resultat(dao, curseur, fichier):
    curseur.fetchone.return_value = None

    assert dao.create_fichier(fichier, audit_id=5) is False
    assert fichier.id == 1  # inchangé


def test_update_fichier_succes(dao, curseur, fichier):
    curseur.rowcount = 1

    assert dao.update_fichier(fichier) is True
    assert curseur.execute.call_args.args[1]["id_fichier"] == 1


def test_update_fichier_introuvable(dao, curseur, fichier):
    curseur.rowcount = 0

    assert dao.update_fichier(fichier) is False


def test_remove_fichier_succes(dao, curseur):
    curseur.rowcount = 1

    assert dao.remove_fichier(1) is True
    assert curseur.execute.call_args.args[1] == {"id": 1}


def test_remove_fichier_introuvable(dao, curseur):
    curseur.rowcount = 0

    assert dao.remove_fichier(99) is False


def test_find_fichier_trouve(dao, curseur):
    curseur.fetchone.return_value = ligne(4)

    f = dao.find_fichier(4)

    assert f.id == 4
    assert f.chemin == "/path/to/file.py"
    assert f.extension == "py"
    assert f.complexite == 5
    assert f.score == 90.0
    assert f.emissionCO2 == 0.5


def test_find_fichier_introuvable(dao, curseur):
    curseur.fetchone.return_value = None

    assert dao.find_fichier(99) is None


def test_find_by_utilisateur(dao, curseur):
    curseur.fetchall.return_value = [ligne(1), ligne(2)]

    fichiers = dao.find_by_utilisateur(3)

    assert [f.id for f in fichiers] == [1, 2]
    assert curseur.execute.call_args.args[1] == {"id_user": 3}


def test_find_by_audit(dao, curseur):
    curseur.fetchall.return_value = [ligne(1)]

    fichiers = dao.find_by_audit(5)

    assert [f.id for f in fichiers] == [1]
    assert curseur.execute.call_args.args[1] == {"id_audit": 5}


def test_find_all(dao, curseur):
    curseur.fetchall.return_value = [ligne(1), ligne(2)]

    fichiers = dao.find_all()

    assert len(fichiers) == 2
    assert fichiers[0].id == 1
    assert fichiers[1].id == 2


def test_find_by_utilisateur_requete_bien_espacee(dao, curseur):
    """Détecte les mots-clés SQL collés au mot précédent (ex: 'uJOIN')."""
    curseur.fetchall.return_value = []

    dao.find_by_utilisateur(3)

    requete = curseur.execute.call_args.args[0]
    assert not re.search(r"\w(FROM|JOIN|WHERE)\b", requete)


@pytest.mark.parametrize(
    "appel",
    [
        lambda dao, fichier: dao.create_fichier(fichier, 1),
        lambda dao, fichier: dao.update_fichier(fichier),
        lambda dao, fichier: dao.remove_fichier(1),
        lambda dao, fichier: dao.find_fichier(1),
        lambda dao, fichier: dao.find_by_utilisateur(1),
        lambda dao, fichier: dao.find_by_audit(1),
        lambda dao, fichier: dao.find_all(),
    ],
    ids=[
        "create",
        "update",
        "remove",
        "find",
        "find_by_util",
        "find_by_audit",
        "find_all",
    ],
)
def test_erreur_bd_remontee(dao, curseur, fichier, appel):
    """Une erreur de la base n'est pas avalée : elle remonte à l'appelant."""
    curseur.execute.side_effect = RuntimeError("base indisponible")

    with pytest.raises(RuntimeError):
        appel(dao, fichier)