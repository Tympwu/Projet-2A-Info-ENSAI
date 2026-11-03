from business_object.vulnerabilite import Vulnerabilite


class Dependances:
    def __init__(self, nom: str, version: str, auteur: str | None) -> None:
        self.nom = nom
        self.auteur = auteur
        self.version = version


def a_vulnerabilite(self, data_api: dict) -> Vulnerabilite | None:
        """Vérifie via les données de l'API si la dépendance présente une vulnérabilité."""
        if not data_api or "vulns" not in data_api:
            return None

        # Si l'API retourne des vulnérabilités pour ce package
        for vuln_data in data_api["vulns"]:
            description = vuln_data.get("details", "Vulnérabilité non spécifiée")
            # Extraction ou attribution d'un score de danger par défaut si non fourni
            score_danger = vuln_data.get("score", 9.5) 
            return Vulnerabilite(description=description, score_danger=score_danger)

        return None
