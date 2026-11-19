import os
from pathlib import Path
from unittest import mock

import dotenv

from dao.db_connection import DBConnection
from dao.utilisateur_dao import UtilisateurDao
from utils.log_utils import get_logger, log
from utils.security import hash_mdp
from utils.singleton import Singleton

logger = get_logger(__name__)


class Manager_db(metaclass=Singleton):
    """
    Database utility
    """

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent.parent

    @log
    def reset_db(self, test_dao=False):
        """Reset la base de donnée
        Si test_dao=True: Reset les jeux de test de donnée
        """
        if test_dao:
            mock.patch.dict(os.environ, {"POSTGRES_SCHEMA": "project_test_dao"}).start()
            pop_data_path = self.base_path / "data" / "pop_db_test.sql"
        else:
            pop_data_path = self.base_path / "data" / "pop_db.sql"

        init_db_path = self.base_path / "data" / "init_db.sql"

        dotenv.load_dotenv()

        schema = os.environ["POSTGRES_SCHEMA"]
        create_schema = f"DROP SCHEMA IF EXISTS {schema} CASCADE; CREATE SCHEMA {schema};"

        # Utilisation de l'objet Path pour lire les fichiers
        try:
            with open(init_db_path, encoding="utf-8") as init_db_file:
                init_db_as_string = init_db_file.read()

            with open(pop_data_path, encoding="utf-8") as pop_db_file:
                pop_db_as_string = pop_db_file.read()
        except FileNotFoundError as e:
            logger.error(f"Erreur de chemin : impossible de trouver le fichier {e.filename}")
            raise

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(create_schema)
                    cursor.execute(init_db_as_string)
                    cursor.execute(pop_db_as_string)
        except Exception as e:
            logger.info(e)
            raise

        for user in UtilisateurDao().find_all():
            user.mot_de_passe = hash_mdp(user.mot_de_passe, user.name)
            UtilisateurDao().update_utilisateur(user)

        return True

