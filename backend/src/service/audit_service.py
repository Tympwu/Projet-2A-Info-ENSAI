from business_object.audit import Audit
from dao.audit_dao import AuditDao
from utils.log_utils import log
from service.analyse_fichier import Analyse_fichier
from service.dossier_service import DossierService

import datetime


class AuditService:
    """Gère la consultation et la suppression de l'audit d'un utilisateur.
    """

    def __init__(self):
        """
        Parameters:
            audit_dao (AuditDao) : Classe DAO spécifique aux audits
            dossier_service (DossierService): Classe Service spécifique aux dossiers
        """
        self.audit_dao = AuditDao()
        self.dossier_service = DossierService()

    @log
    def find_audit(self, id_audit: int) -> Audit | None:
        """Retourne un audit spécifique.

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            Audit | None: L'audit demandé, None si ce dernier n'a pas été trouvé.
        """
        audit = self.audit_dao.find_audit(id_audit)
        return audit

    @log
    def create_audit(self, chemin_dossier: str) -> Audit:
        """Créer un audit en se basant sur le chemin d'accès du dossier

        Args:
            chemin_dossier (str): Chemin d'accès du dossier contenant les fichiers.

        Returns:
            Audit: L'audit nouvellement crée, None si il y a eu un échec dans la création.
        Raises:
            ValueError: Le chemin indiqué ne mène à aucun dossier
        """
        dossier = self.dossier_service.consulter_dossier(chemin_dossier)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return self.dossier_service.traiter_dossier(dossier)


    @log
    def remove_audit(self, id_audit: int) -> bool:
        """Supprime un audit spécifié via son ID.

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            bool: True si la suppression à réusie, False sinon
        """
        audit = self.find_audit(id_audit)
        if not audit:
            return False
        return self.audit_dao.remove_audit(audit)

    @log
    def find_all_audit(self) -> list[Audit]:
        """Renvoie tous les audits de la base de données.
        Returns:
            list[Audit]: Liste composée de tous les audits enregistrés. La liste est vide si aucun audit est trouvé"""
        return self.audit_dao.find_all()
