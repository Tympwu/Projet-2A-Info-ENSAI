from pathlib import Path

from business_object.vulnerabilite import Vulnerabilite


class Fichier:
    """
    Représente un fichier source d'un dossier soumis à l'audit.

    Un fichier permet de lire son contenu (en entier ou ligne par ligne)
    et d'en extraire les dépendances. Il stocke aussi les résultats de
    l'audit le concernant : vulnérabilités détectées, complexité, score
    et émissions de CO2e estimées.

    Attributes:
        id (int): Identifiant unique du fichier.
        chemin (str): Chemin d'accès au fichier.
        nom (str): Nom du fichier.
        extension (str): Extension du fichier, par exemple ".py"
            (déduite du chemin).
        liste_vulnerabilites (list[Vulnerabilite] | None): Vulnérabilités
            détectées, ou None tant que l'analyse n'a pas eu lieu.
        complexite (str | None): Niveau de complexité du code, ou None
            avant analyse.
        score (float | None): Score du fichier, ou None avant analyse.
        emissionCO2 (float | None): Émissions de CO2 estimées, ou None
            avant analyse.
    """

    def __init__(
        self,
        id: int,
        nom: str,
        chemin: str,
        liste_vulnerabilites: list[Vulnerabilite] | None = None,
        complexite: str | None = None,
        score: float | None = None,
        emissionCO2: float | None = None,
    ) -> None:
        self.id = id
        self.chemin = chemin
        self.nom = Path(chemin).name
        self.extension = Path(chemin).suffix
        self.liste_vulnerabilites = liste_vulnerabilites
        self.complexite = complexite
        self.score = score
        self.emissionCO2 = emissionCO2
