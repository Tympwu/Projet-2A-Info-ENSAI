from business_object.vulnerabilites import Vulnerabilites


class Dependances:
    def __init__(self, nom: str, version: str, auteur: str | None) -> None:
        self.nom = nom
        self.auteur = auteur
        self.version = version

    def a_vulnerabilite(self, data_api: dict) -> Vulnerabilites | None:
        """Vérifie via les données de l'API si la dépendance présente une vulnérabilité."""
        pass
