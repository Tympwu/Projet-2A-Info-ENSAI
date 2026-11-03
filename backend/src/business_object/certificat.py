from datetime import datetime


class Certificat:
    def __init__(
        self,
        id: int,
        nom: str,
        date_delivrance: datetime | None = None,
    ) -> None:
        self.id = id
        self.nom = nom
        self.date_delivrance = date_delivrance
        self.statut = "en attente"

    def calcul_QualityGate(self, audit) -> bool:
        """Vérifie si l'audit remplit les critères de qualité pour valider le certificat."""
        if audit is None or not audit.statut:
            self.statut = "rejeté"
            return False

        # Exemple de règle : score global supérieur ou égal à 5.0 (sur 10) et pas de critique bloquante
        if audit.score is not None and audit.score < 5.0:
            self.statut = "validé"
            return True

        self.statut = "échoué"
        return False
