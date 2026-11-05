from datetime import datetime

from business_object.audit import Audit
from business_object.certificat import Certificat
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from dao.audit_dao import AuditDao
from dao.fichier_dao import FichierDao
from dao.manager_db import Manager_db
from service.analyse_fichier import Analyse_fichier
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class DossierService:
    """Classe de service gérant l'analyse des dossiers et des fichiers"""

    def __init__(self) -> None:
        self.api_url_OSV: str = "https://api.osv.dev/v1/query"  # URL pour l'API de vulnérabilités
        self.fichier_dao = FichierDao()
        self.audit_dao = AuditDao()
        self.audit_service = Analyse_fichier()

    @log
    def find_all_fichier(self) -> list[Fichier]:
        """Renvoie la liste de tous les Fichiers stockés
        Returns:
            list[Fichier]: Liste de fichiers contenus dans la base de données
        """
        return self.fichier_dao.find_all()

    @log
    def find_fichier_by_id(self, id_fichier: int) -> Fichier | None:
        """Recherche et retourne un fichier par son identifiant unique via le DAO."""
        return self.fichier_dao.find_fichier(id_fichier)

    @log
    def remove_fichier(self, id_fichier: int) -> bool:
        """Supprime un fichier de la base de donnée
        Args:
            id_fichier (int): ID du fichier à supprimer
        Returns:
            bool : True si la supression est réussie, False sinon
        """
        return self.fichier_dao.remove_fichier(id_fichier)

    @log
    def update_fichier(self, fichier: Fichier, id_audit: int = None) -> Fichier | None:
        """Met à jour un fichier en utilisant son ID et les données d'un autre objet fichier
        Args:
            id_audit (int) = None: ID de l'audit dans lequel est le fichier. Vaut None initialement
            fichier (Fichier): Données à utiliser pour mettre le fichier à jour
        Returns:
            Fichier | None: Fichier modifié, None si échec de la modification
        """
        success = self.fichier_dao.update_fichier(fichier=fichier, id_audit=id_audit)
        if not success:
            return None
        else:
            return self.find_fichier_by_id(id_fichier=fichier.id)

    @log
    def create_dossier(self, liste_fichier: list[Fichier]) -> bool:
        """Créer et enregistre les fichiers d'un dossier en base de données."""
        success = True
        for fichier in liste_fichier:
            res = self.fichier_dao.create_fichier(fichier)
            if not res:
                success = False
        return success

    @log
    def remove_dossier(self, path: str) -> bool:
        """Supprime l'ensemble des fichiers contenus dans le dossier indiqué
        Args:
            path (str): Chemin d'accès au dossier
        Returns:
            bool : True si la suppression réussie, False sinon
        """
        return self.fichier_dao.remove_dossier(path)

    @log
    def update_dossier(self, path: str, dossier: Dossier) -> bool:
        """Met à jour un dossier à l'adresse fourni, avec un nouveau dossier donné
        Le dossier à mettre à jour ne doit pas avoir été traité i.e. ne doit pas avoir d'audit correspondant
        Sinon, il faut plutôt recréer un dossier et un audit

        Args:
            path (str): Chemin d'accès à l'ancien dossier
            dossier (Dossier): Nouvelles données qui remplaceront l'ancien dossier
        Returns:
            bool : True si la suppression réussie, False sinon
        Raise:
            ValueError : L'adresse fourni du premier dossier n'est pas valide
        """
        dossier_init = self.fichier_dao.read_dossier(path)
        if dossier_init:
            return self.fichier_dao.update_dossier(dossier_init, dossier_nouv=dossier)
        else:
            raise ValueError("L'adresse fourni du premier dossier n'est pas valide")

    @log
    def consulter_dossier(self, path: str) -> Dossier | None:
        """Renvoie un objet de type dossier correspondant à l'ensemble des fichiers stockés à cet endroit
        Args:
            path (str): Chemin d'accès au dossier
        Returns:
            Dossier | None : Dossier contenant toutes les informations des fichiers issus de ce chemin, None si aucun
        """
        return self.fichier_dao.read_dossier(path)

    @log
    def traiter_emission_dossier(self, audit: Audit, n: int = 500) -> Audit:
        """Analyse l'impact écologique du dossier compris dans l'audit
        Args:
            audit (Audit): Audit contenant le dossier dont l'analyse énergétique va être faire
            n (int) = 500: Taille de l'entrée prise comme référence
        Returns:
            Audit : Objet initial avec l'information en plus sur la consommation énergétique du projet en général
        """
        audit.emissionCO2_total = 0
        for fichier in audit.dossier.liste_fichiers:
            fichier.emissionCO2 = self.audit_service.calculer_emissionCO2e(fichier, nb_operations=n)
            if isinstance(fichier.emissionCO2):
                audit.emissionCO2_total += fichier.emissionCO2
        if audit.emissionCO2_total == 0:
            logger.warning("Echec du calcul des emissions CO2 de l'audit")
        return audit

    @log
    def traiter_dossier(self, dossier: Dossier, id_utilisateur: int | None = None) -> Audit | None:
        """Traite un dossier complet pour lancer l'audit de ses fichiers.
        Args:
            dossier (Dossier): Dossier à analyser pour l'audit
        Returns:
            Audit: Audit final obtenu lors de l'analyse
        """
        # Création de l'audit
        audit = Audit(dossier=dossier, date=datetime.today())
        if not self.audit_dao.create_audit(audit, id_utilisateur):
            logger.error("Création de l'audit impossible")
            return None

        # Analyse fichier par fichiers
        for fichier in dossier.liste_fichiers:
            try:
                # Extraction de chacune des dépendances des fichiers
                if not fichier.extraire_dependances():
                    logger.error("Le type de fichier est invalide ou illisible")
                    return None
            # Si le fichier n'est pas trouvé
            except FileNotFoundError:
                logger.error("Fichier de l'audit introuvable")
                return None

            # Analyse des anti_patterns
            anti_pattern = self.audit_service.detecter_anti_patterns(fichier)

            if not anti_pattern:
                logger.error("Analyse des anti-patterns échoué")
                return None
            else:
                fichier.liste_anti_pattern = anti_pattern

            # Calcul du score basé sur les dépendances
            if not self.audit_service.analyse_dependances(fichier):
                logger.error("Echec du calcul des scores des dépendances")
                return None

        try:
            audit.calculer_score()
        except ValueError:
            logger.error("Erreur lors du calcul général de l'audit")
        return audit

    @log
    def generer_et_exporter_certificat(self, audit: Audit, exporter: bool = False) -> Certificat:
        """Génère le certificat de l'audit et l'exporte si demandé.
        Args:
            audit (Audit): Audit à utiliser pour la création du certificat
            exporter (bool) = False: Paramètre indiquant la nécessité d'exporter le certificat dans un fichier pdf
        Return:
            Certificat: Certificat généré suite à l'Audit
        """
        certificat = Certificat(audit=audit, date_delivrance=datetime.today())
        if exporter:
            Manager_db().write_certificate(certificat)
        return certificat
