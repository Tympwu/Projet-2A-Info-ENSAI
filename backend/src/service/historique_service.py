from business_object.historique import Historique
from dao.audit_dao import AuditDao
from utils.log_utils import log


class Historique_service:

    def __init__(self, audit_dao: AuditDao) -> None:
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
        self.verifier_id(id_utilisateur, "id_utilisateur")
        audits = self.audit_dao.find_by_utilisateur(id_utilisateur)
        return Historique(id=id_utilisateur, audits=audits)

    @log
    def supprimer_audit_historique(self, id_audit: int) -> bool:
        self.verifier_id(id_audit, "id_audit")
        audit = self.audit_dao.find_audit(id_audit)
        if audit is None:
            return False
        return self.audit_dao.remove_audit(audit)

    @log
    def supprimer_historique(self, id_utilisateur: int) -> bool:
        self.verifier_id(id_utilisateur, "id_utilisateur")
        audits = self.audit_dao.find_audit(id_utilisateur)
        if audits is None:
            return False
        resultats = [self.audit_dao.remove_audit(audit) for audit in audits]
        return all(resultats)
