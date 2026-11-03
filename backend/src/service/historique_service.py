from business_object.historique import Historique
from dao.audit_dao import AuditDao
from utils.log_utils import log


class Historique_service:
    """Gère la consultation et la suppression de l'historique d'un utilisateur.

    L'historique n'est pas stocké comme tel : c'est l'ensemble des audits
    d'un utilisateur. Le service le reconstruit à partir de `AuditDao`,
    après avoir validé les arguments. Il ne contient aucune requête SQL.

    Attributes:
        audit_dao (AuditDao): DAO utilisé pour lire et supprimer les audits.
    """

    def __init__(self, audit_dao: AuditDao) -> None:
        """Initialise le service.

        Args:
            audit_dao (AuditDao): DAO des audits
        """
        self.audit_dao = audit_dao

    @staticmethod
    def verifier_id(valeur: int, nom: str) -> None:
        """Vérifie qu'un identifiant est un entier strictement positif.

        Args:
            valeur (int): Valeur à contrôler.
            nom (str): Nom de l'argument, utilisé dans le message d'erreur.

        Raises:
            ValueError: Si `valeur` n'est pas un entier supérieur ou égal
                à 1.
        """
        if not isinstance(valeur, int) or valeur < 1:
            raise ValueError(f"{nom} doit être un entier positif")

    @log
    def consulter_historique(self, id_utilisateur: int) -> None:
        """Retourne l'historique des audits d'un utilisateur.

        Args:
            id_utilisateur (int): Identifiant de l'utilisateur.

        Returns:
            Historique: L'historique de l'utilisateur. Sa liste d'audits
            est vide si l'utilisateur n'a réalisé aucun audit.

        Raises:
            ValueError: Si `id_utilisateur` n'est pas un entier positif.
        """
        self.verifier_id(id_utilisateur, "id_utilisateur")
        audits = self.audit_dao.find_by_utilisateur(id_utilisateur)
        return Historique(id=id_utilisateur, audits=audits)

    @log
    def supprimer_audit_historique(self, id_audit: int) -> bool:
        """Supprime un audit de l'historique.

        Args:
            id_audit (int): Identifiant de l'audit à supprimer.

        Returns:
            bool: True si l'audit a été supprimé, False s'il n'existe pas
            ou si la suppression a échoué.

        Raises:
            ValueError: Si `id_audit` n'est pas un entier positif.
        """
        self.verifier_id(id_audit, "id_audit")
        audit = self.audit_dao.find_audit(id_audit)
        if audit is None:
            return False
        return self.audit_dao.remove_audit(audit)

    @log
    def supprimer_historique(self, id_utilisateur: int) -> bool:
        """Supprime tous les audits d'un utilisateur.

        Args:
            id_utilisateur (int): Identifiant de l'utilisateur.

        Returns:
            bool: True si tous les audits ont été supprimés, False si
            l'utilisateur n'a aucun audit ou si au moins une suppression
            a échoué.

        Raises:
            ValueError: Si `id_utilisateur` n'est pas un entier positif.
        """
        self.verifier_id(id_utilisateur, "id_utilisateur")
        audits = self.audit_dao.find_audit(id_utilisateur)
        if audits is None:
            return False
        resultats = [self.audit_dao.remove_audit(audit) for audit in audits]
        return all(resultats)
