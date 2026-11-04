"""Tests unitaires de DBConnection."""

import os
from unittest.mock import patch

import psycopg2
import pytest
from psycopg2.extras import RealDictCursor

from dao.db_connection import DBConnection
from utils.singleton import Singleton

VARIABLES = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DATABASE": "ma_base",
    "POSTGRES_USER": "mon_user",
    "POSTGRES_PASSWORD": "mon_mdp",
    "POSTGRES_SCHEMA": "mon_schema",
}


@patch.dict(os.environ, VARIABLES)  # Vérifie que les variables sont branchées sur les bons paramètres
@patch("dao.db_connection.psycopg2.connect")
def test_init_ouvre_la_connexion_avec_les_variables_d_environnement(connect):
    type.__call__(DBConnection)

    connect.assert_called_once_with(
        host="localhost",
        port="5432",
        database="ma_base",
        user="mon_user",
        password="mon_mdp",
        options="-c search_path=mon_schema",
        cursor_factory=RealDictCursor,
    )


@pytest.mark.parametrize("manquante", list(VARIABLES), ids=list(VARIABLES))
@patch("dao.db_connection.psycopg2.connect")
def test_init_variable_manquante(connect, manquante):
    """Chaque variable est obligatoire : sans elle, aucune connexion n'est tentée.
    On fait la connection sans une de ces variables et on vérifie bien que connect
    n'est pas appelé"""
    environnement = {k: v for k, v in VARIABLES.items() if k != manquante}

    with patch.dict(os.environ, environnement, clear=True):
        with pytest.raises(KeyError):
            type.__call__(DBConnection)

    connect.assert_not_called()


@patch.dict(os.environ, VARIABLES)
@patch("dao.db_connection.psycopg2.connect")
def test_init_erreur_de_connexion_remontee(connect):
    connect.side_effect = psycopg2.OperationalError("connexion refusée")

    with pytest.raises(psycopg2.OperationalError):
        type.__call__(DBConnection)


@patch.dict(os.environ, VARIABLES)
@patch("dao.db_connection.psycopg2.connect")
def test_connection_renvoie_la_connexion_ouverte(connect):
    instance = type.__call__(DBConnection)

    assert instance.connection is connect.return_value


@patch.dict(os.environ, VARIABLES)
@patch("dao.db_connection.psycopg2.connect")
def test_connection_est_en_lecture_seule(connect):
    instance = type.__call__(DBConnection)

    with pytest.raises(AttributeError):
        instance.connection = "autre connexion"


def test_dbconnection_utilise_le_pattern_singleton():
    """DBConnection est construite par la métaclasse Singleton.

    Le comportement du Singleton lui-même (« deux appels, une seule
    instance ») se teste à part, dans un test de `utils.singleton`.
    """
    assert type(DBConnection) is Singleton
