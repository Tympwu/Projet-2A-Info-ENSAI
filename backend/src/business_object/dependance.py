from business_object.vulnerabilite import Vulnerabilite


class Dependances:
    def __init__(self, nom: str, version: str, auteur: str | None) -> None:
        self.nom: str = nom
        self.auteur: str = auteur
        self.version: str = version

    def a_vulnerabilite(
        self,
        data_api: dict,
        scores: list[float | None],
        seuil: float = 7.0,
    ) -> list[Vulnerabilite]:
        """
        Construit les vulnérabilités retenues pour cette dépendance.

        data_api : réponse OSV contenant la clé "vulns".
        scores : scores calculés pour chaque fiche OSV.
        seuil : gravité minimale retenue.
        """

        vulnerabilites = []
        fiches = data_api.get("vulns", [])

        if len(fiches) != len(scores):
            raise ValueError("Chaque fiche OSV doit avoir un score associé.")

        for fiche, score in zip(fiches, scores, strict=False):
            if score is None or score < seuil:
                continue

            identifiant = fiche.get("id", "identifiant inconnu")
            description = fiche.get("summary") or fiche.get("details") or "Description indisponible"

            vulnerabilites.append(
                Vulnerabilite(
                    description=f"{identifiant} : {description}",
                    score_danger=score,
                )
            )

        return vulnerabilites
