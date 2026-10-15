from business_object.audit import Audit
from business_object.certificat import Certificat
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from dao.fichier_dao import FichierDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class Fichier_service:
    """Classe de service gérant l'analyse des dossiers, des fichiers et des audits."""

    def __init__(self) -> None:
        self.api_url_OSV: str = "https://api.osv.dev/v1/query"  # URL pour l'API de vulnérabilités
        self.fichier_dao = FichierDao()

    @log
    def traiter_dossier_audit(self, dossier: Dossier) -> Audit:
        """Traite un dossier complet pour lancer l'audit de ses fichiers."""
        # Logique d'orchestration : parcours du dossier, analyse des fichiers et enregistrement
        pass

    @log
    def analyse_complexite(self, audit: Audit) -> Audit:
        """Analyse la complexité du code pour l'audit en cours."""
        pass

    @log
    def generer_et_exporter_certificat(
        self, audit: Audit, exporter: bool
    ) -> Certificat:
        """Génère le certificat de l'audit et l'exporte si demandé."""
        pass

    @log
    def find_fichier_by_id(self, id_fichier: int) -> Fichier | None:
        """Recherche et retourne un fichier par son identifiant unique via le DAO."""
        return self.fichier_dao.find_fichier(id_fichier)

    @log
    def create_dossier(self, liste_fichier: list[Fichier], audit_id: int) -> bool:
        """Crée et enregistre les fichiers d'un dossier en base de données."""
        success = True
        for fichier in liste_fichier:
            res = self.fichier_dao.create_fichier(fichier, audit_id)
            if not res:
                success = False
        return success