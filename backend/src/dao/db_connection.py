import os

import psycopg2
from psycopg2.extras import RealDictCursor

from utils.singleton import Singleton


class DBConnection(metaclass=Singleton):
    """Classe de connexion avec la base de données utilisant le pattern Singleton

    Cette classe assure qu'une unique connexion à la base de données PostgreSQL est
    ouverte et utilisé dans l'application

    Attributs :
        connection : La connexion active à la base de donnée
    """

    def __init__(self):
        """Initialise la connexion avec la base de données en utilisant les variables d'environnement
        Raises:
            KeyError: Si une variable nécessaire pour la connexion est manquante.
            psycopg2.Error: Si la connexion avec la base de donnée échoue.
        """

        self.__connection = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            database=os.environ["POSTGRES_DATABASE"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            options=f"-c search_path={os.environ['POSTGRES_SCHEMA']}",
            cursor_factory=RealDictCursor,
        )

    @property
    def connection(self):
        """Donne accès à la connexion à la base de données
        Returns:
            La connexion établie avec la base de donnée.
        """
        return self.__connection
