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
        # pas encore mais ajouter les vérifications ici
        pass
