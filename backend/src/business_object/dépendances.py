from business_object.vulnerabilite import Vulnerabilite


class Dependances:
    def __init__(self, nom: str, version: str, auteur: str | None) -> None:
        self.nom = nom
        self.auteur = auteur
        self.version = version

    def a_vulnerabilite(self, data_api: dict) -> Vulnerabilite | None:
        """Vérifie via les données de l'API si la dépendance présente une vulnérabilité."""
        pass
