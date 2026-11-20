"""Tests unitaires de AuditDao."""

import re
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dao.audit_dao import AuditDao

DATE = datetime(2026, 11, 3, 10, 30)


@pytest.fixture
def curseur():
    """Remplace la connexion à la base par un faux curseur.

    Le DAO écrit `with DBConnection().connection as connection` puis
    `with connection.cursor() as cursor`. On configure donc la chaîne
    de faux objets correspondante et on renvoie le dernier maillon :
    le curseur, que chaque test règle à sa convenance.
    """
    with patch("dao.audit_dao.DBConnection") as faux_db:
        connexion = faux_db.return_value.connection.__enter__.return_value
        yield connexion.cursor.return_value.__enter__.return_value


@pytest.fixture
def faux_fichier_dao():
    """Remplace FichierDao, qui n'est pas l'objet de ces tests."""
    with patch("dao.audit_dao.FichierDao") as faux:
        faux.return_value.find_by_audit.return_value = ["fichier_1"]
        yield faux.return_value


@pytest.fixture
def dao():
    """Retourne le DAO testé (c'est un singleton)."""
    return AuditDao()


@pytest.fixture
def audit():
    """Retourne un audit minimal avec les attributs que le DAO lit."""
    return SimpleNamespace(
        id=1,
        date=DATE,
        statut="TERMINE",
        score=85.0,
        emissionCO2_total=1.2,
        dossier=SimpleNamespace(liste_fichiers=[]),  # update_audit met aussi à jour les fichiers
    )


def ligne(id_audit=1):
    """Retourne une ligne telle que la base la renverrait pour un audit."""
    return {
        "id": id_audit,
        "date_audit": DATE,
        "statut": "TERMINE",
        "score": 85.0,
        "emissionco2": 1.2,
    }


def test_create_audit_succes(dao, curseur, audit):
    curseur.fetchone.return_value = {"id": 7}

    assert dao.create_audit(audit, utilisateur_id=3) is True

    assert audit.id == 7  # l'identifiant généré par la base est récupéré
    parametres = curseur.execute.call_args.args[1]
    assert parametres["utilisateur_id"] == 3
    assert parametres["statut"] == "TERMINE"
    assert parametres["emissionCO2"] == 1.2


def test_create_audit_sans_resultat(dao, curseur, audit):
    curseur.fetchone.return_value = None

    assert dao.create_audit(audit, utilisateur_id=3) is False
    assert audit.id == 1  # inchangé


def test_update_audit_succes(dao, curseur, audit):
    curseur.rowcount = 1

    assert dao.update_audit(audit) is True
    assert curseur.execute.call_args.args[1]["id"] == 1


def test_update_audit_introuvable(dao, curseur, audit):
    curseur.rowcount = 0

    assert dao.update_audit(audit) is False


def test_update_audit_rattache_ses_fichiers(dao, curseur, audit, faux_fichier_dao):
    """Chaque fichier du dossier est rattaché à l'audit en base."""
    curseur.rowcount = 1
    fichiers = ["fichier_1", "fichier_2"]
    audit.dossier = SimpleNamespace(liste_fichiers=fichiers)

    assert dao.update_audit(audit) is True

    appels = faux_fichier_dao.update_fichier.call_args_list
    assert [(a.args[0], a.kwargs["id_audit"]) for a in appels] == [
        ("fichier_1", 1),
        ("fichier_2", 1),
    ]


def test_remove_audit_succes(dao, curseur, audit):
    curseur.rowcount = 1

    assert dao.remove_audit(audit) is True
    assert curseur.execute.call_args.args[1] == {"id": 1}


def test_remove_audit_introuvable(dao, curseur, audit):
    curseur.rowcount = 0

    assert dao.remove_audit(audit) is False


def test_find_audit_trouve(dao, curseur, faux_fichier_dao):
    curseur.fetchone.return_value = ligne(3)

    audit = dao.find_audit(3)

    assert audit.id == 3
    assert audit.statut == "TERMINE"
    assert audit.score == 85.0
    assert audit.emissionCO2_total == 1.2
    assert audit.dossier.liste_fichiers == ["fichier_1"]
    faux_fichier_dao.find_by_audit.assert_called_once_with(3)


def test_find_audit_introuvable(dao, curseur, faux_fichier_dao):
    curseur.fetchone.return_value = None

    assert dao.find_audit(99) is None
    faux_fichier_dao.find_by_audit.assert_not_called()


def test_find_by_utilisateur_plusieurs_audits(dao, curseur, faux_fichier_dao):
    curseur.fetchall.return_value = [ligne(1), ligne(2)]

    audits = dao.find_by_utilisateur(3)

    assert [a.id for a in audits] == [1, 2]
    assert curseur.execute.call_args.args[1] == {"id_utilisateur": 3}


def test_find_by_utilisateur_aucun_audit(dao, curseur, faux_fichier_dao):
    curseur.fetchall.return_value = []

    assert dao.find_by_utilisateur(3) == []


def test_find_by_utilisateur_requete_bien_espacee(dao, curseur):
    """Détecte les mots-clés SQL collés au mot précédent ("uJOIN").

    Une requête écrite en plusieurs morceaux de texte oublie facilement
    l'espace final de chaque morceau. Les mocks ne comprennent pas le SQL,
    donc on vérifie ce défaut courant à la main.
    """
    curseur.fetchall.return_value = []

    dao.find_by_utilisateur(3)

    requete = curseur.execute.call_args.args[0]
    assert not re.search(r"\w(FROM|JOIN|WHERE)\b", requete)


@pytest.mark.parametrize(
    "appel",
    [
        lambda dao, audit: dao.create_audit(audit, 1),
        lambda dao, audit: dao.update_audit(audit),
        lambda dao, audit: dao.remove_audit(audit),
        lambda dao, audit: dao.find_audit(1),
        lambda dao, audit: dao.find_by_utilisateur(1),
    ],
    ids=["create", "update", "remove", "find", "find_by_utilisateur"],
)
def test_erreur_bd_remontee(dao, curseur, audit, appel):
    """Une erreur de la base n'est pas avalée : elle remonte à l'appelant."""
    curseur.execute.side_effect = RuntimeError("base indisponible")

    with pytest.raises(RuntimeError):
        appel(dao, audit)


def test_find_all_plusieurs_audits(dao, curseur, faux_fichier_dao):
    curseur.fetchall.return_value = [ligne(1), ligne(2)]
    audits = dao.find_all()
    assert [a.id for a in audits] == [1, 2]


def test_find_all_aucun_audit(dao, curseur, faux_fichier_dao):
    curseur.fetchall.return_value = []
    assert dao.find_all() == []
