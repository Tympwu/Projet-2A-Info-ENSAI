from datetime import datetime

from business_object.audit import Audit
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from dao.audit_dao import AuditDao
from dao.fichier_dao import FichierDao
from service.analyse_fichier import Analyse_fichier
from service.utilisateur_service import UtilisateurService
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class DossierService:
    """Classe de service gérant l'analyse des dossiers et des fichiers"""

    def __init__(self) -> None:
        self.api_url_OSV: str = "https://api.osv.dev/v1/query"  # URL pour l'API de vulnérabilités
        self.fichier_dao = FichierDao()
        self.audit_dao = AuditDao()
        self.analyse_fichier = Analyse_fichier()

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
    def find_fichier_by_user(self, id_utilisateur: int) -> list[Fichier] | None:
        """Permet de retrouver l'ensemble des fichiers créer par un utilisateur
        Args:
            id_utilisateur (int): ID de l'utilisateur pour lequel on recherche les fichiers
        Returns:
            list[Fichier] | None: Liste de fichiers spécifiques à l'utilisateur. Renvoie None si l'utilisateur est introuvable
        """
        try:
            fichiers = self.fichier_dao.find_by_utilisateur(id_utilisateur)
        except ValueError:
            return None
        return fichiers

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
        try:
            success = self.fichier_dao.update_fichier(fichier=fichier, id_audit=id_audit)
        except ValueError:
            return None
        if not success:
            return None
        else:
            return self.find_fichier_by_id(id_fichier=fichier.id)

    @log
    def create_fichier(self, fichier: Fichier) -> Fichier | None:
        """Créer un fichier et le stocke dans la base de donnée
        Args:
            fichier (Fichier): Objet de type fichier
        Returns:
            Fichier | None: Fichier créé, None si échec
        """
        if self.fichier_dao.create_fichier(fichier):
            return fichier
        else:
            return None

    @log
    def consulter_dossier(self, id_audit: int) -> Dossier | None:
        """Renvoie un objet de type dossier correspondant à l'ensemble des fichiers stockés à cet endroit
        Args:
            id_audit (int): Audit contenant le dossier
        Returns:
            Dossier | None : Dossier contenant toutes les informations des fichiers issus de cet audit, None si aucun
        """
        return self.fichier_dao.read_dossier(id_audit)

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
            # Seuls les fichiers Python ont une complexité, donc des émissions estimables.
            if fichier.extension != ".py":
                continue
            fichier.emissionCO2 = self.analyse_fichier.estimer_emission_fichier(
                fichier, taille_reference=n
            )
            if isinstance(fichier.emissionCO2, (int, float)):
                audit.emissionCO2_total += fichier.emissionCO2
        if audit.emissionCO2_total == 0:
            logger.warning("Echec du calcul des emissions CO2 de l'audit")
        return audit

    @log
    def traiter_dossier(self, dossier: Dossier) -> Audit | None:
        """Traite un dossier complet pour lancer l'audit de ses fichiers.
        - Récupération de l'ID de l'utilisateur connecté (ou pas)
        - Création d'un objet Audit et enregistrement dans la base de donnée
        - Puis fichier par fichiers :
            - Extraction des dépendances en local (dans l'objet fichier)
            - Analyse des anti-patterns présent dans le fichier et stockage en local
            - Calcul du score affecté au fichier
        - Calcul final de l'audit
        Args:
            dossier (Dossier): Dossier à analyser pour l'audit
        Returns:
            Audit: Audit final obtenu lors de l'analyse
        Raises:
            ValueError: Analyse des anti-patterns échouée
            ArithmeticError: Echec du calcul des scores des dépendances
            ArithmeticError: Erreur lors du calcul général de l'audit
            FileNotFoundError: Le fichier est invalide ou illisible
            FileNotFoundError Le fichier est introuvable
        """

        # Récupération de l'ID si un utilisateur est connecté
        id_utilisateur = UtilisateurService().utilisateur_connecte
        if id_utilisateur:
            id_utilisateur = id_utilisateur.id

        print("Intro 1 OK")
        # Création de l'audit
        audit = Audit(dossier=dossier, date=datetime.today())
        if not self.audit_dao.create_audit(audit, id_utilisateur):
            logger.error("Création de l'audit impossible")
            return None

        print("Intro 2 OK\nPassage aux traitement fichier par fichier :\n")
        # Analyse fichier par fichiers
        for fichier in dossier.liste_fichiers:
            try:
                # Extraction de chacune des dépendances des fichiers
                if not fichier.extraire_dependances():
                    logger.error("Le type de fichier est invalide ou illisible")
                    raise FileNotFoundError("Le fichier est invalide ou illisible")
            # Si le fichier n'est pas trouvé
            except FileNotFoundError:
                logger.error("Fichier de l'audit introuvable")
                raise FileNotFoundError("Le fichier est introuvable") from FileNotFoundError
            print("étape 1 OK")

            if fichier.extension == ".py":
                # Analyse des anti_patterns
                anti_pattern = self.analyse_fichier.detecter_anti_patterns(fichier)

                if anti_pattern is None:
                    logger.error("Analyse des anti-patterns échouée")
                    raise ValueError("Analyse des anti-patterns échouée")
                else:
                    fichier.liste_anti_pattern = anti_pattern
                print("etape 2 OK", anti_pattern)

            # Calcul du score basé sur les dépendances
            if not self.analyse_fichier.analyse_dependances(fichier):
                logger.error("Echec du calcul des scores des dépendances")
                raise ArithmeticError("Echec du calcul des scores des dépendances")
            print("etape 3 OK")

        try:
            audit.lancer()
        except ValueError:
            logger.error("Erreur lors du calcul général de l'audit")
            raise ArithmeticError("Erreur lors du calcul général de l'audit") from ValueError
        print("etape 4 OK")

        # Enregistrement de l'audit dans la base de donnée
        if not self.audit_dao.update_audit(audit):
            raise ValueError("Erreur lors du stockage dans la base de donnée")
        print("etape 5 OK")

        return audit
