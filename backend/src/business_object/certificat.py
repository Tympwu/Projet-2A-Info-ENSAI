from datetime import datetime

from business_object.audit import Audit


class Certificat:
    def __init__(
        self,
        audit: Audit,
        date_delivrance: datetime | None = None,
    ) -> None:
        self.id = audit.id
        self.nom = audit.dossier.nom
        self.date_delivrance = date_delivrance
        self.statut = "en attente"
        self.audit = audit

    def calcul_QualityGate(self) -> bool:
        """Vérifie si l'audit remplit les critères de qualité pour valider le certificat."""
        if self.audit is None or not self.audit.statut:
            self.statut = "rejeté"
            return False

        # Exemple de règle : score global supérieur ou égal à 5.0 (sur 10) et pas de critique bloquante
        if self.audit.score is not None and self.audit.score < 5.0:
            self.statut = "validé"
            return True

        self.statut = "échoué"
        return False
