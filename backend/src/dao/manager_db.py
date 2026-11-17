import json
import os
from pathlib import Path
from unittest import mock

import dotenv

from business_object.audit import Audit
from business_object.certificat import Certificat
from business_object.sbom import SBOM
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
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

        return True

    @log
    def write_certificate(self, certificat: Certificat) -> Path:
        """Exporte un certificat dans un fichier JSON."""
        dossier_export = self.base_path / "data" / "certificats"
        dossier_export.mkdir(parents=True, exist_ok=True)
        chemin_fichier = dossier_export / f"certificat_{certificat.id}.json"

        contenu = {
            "audit_id": certificat.id,
            "nom": certificat.nom,
            "date_delivrance": (
                certificat.date_delivrance.isoformat()
                if certificat.date_delivrance is not None
                else None
            ),
            "statut": certificat.statut,
        }

        try:
            with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                json.dump(contenu, fichier, ensure_ascii=False, indent=4)

            logger.info(f"Certificat exporté avec succès dans le fichier {chemin_fichier}")
            return chemin_fichier

        except OSError:
            logger.exception("Erreur lors de l'exportation du certificat")
            raise

    @log
    def exporter_SBOM(self, sbom: SBOM, audit: Audit) -> Path:
        """Exporte le SBOM d'un audit dans un fichier JSON."""
        dossier_export = self.base_path / "data" / "sbom"
        dossier_export.mkdir(parents=True, exist_ok=True)
        chemin_fichier = dossier_export / f"sbom_audit_{audit.id}.json"

        try:
            contenu = sbom.generer_sbom(audit)

            with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                fichier.write(contenu)

            logger.info(f"SBOM exporté avec succès dans le fichier {chemin_fichier}")
            return chemin_fichier

        except (OSError, ValueError, TypeError):
            logger.exception("Erreur lors de l'exportation du SBOM")
            raise
