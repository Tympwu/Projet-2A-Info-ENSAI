class Vulnerabilite:
    """
    Représente une vulnérabilité de sécurité détectée dans un projet.

    Une vulnérabilité est décrite par un texte et un score de danger sur
    l'échelle CVSS (0 à 10). Elle est considérée comme critique à partir de
    9.0, seuil de la catégorie « critique » de l'échelle CVSS v3.

    Attributes
    ----------
    seuil_critique (float): Score à partir duquel une vulnérabilité est critique.
    description (str): Description de la vulnérabilité.
    score_danger (float): Score de danger, compris entre 0 et 10.
    """

    seuil_critique: float = 9.0

    def __init__(self, description: str, score_danger: float) -> None:
        """
        Initialise une vulnérabilité.

        Paramètres
        ----------
        description (str): Description de la vulnérabilité.
        score_danger (float): Score de danger, entre 0 et 10 inclus.

        Raises
        ------
        ValueError: Si `score_danger` n'est pas compris entre 0 et 10.
        """
        if not 0 <= score_danger <= 10:
            raise ValueError(f"score_danger doit être entre 0 et 10, reçu : {score_danger}")
        self.description = description
        self.score_danger = score_danger

    def est_critique(self) -> bool:
        """
        Indique si la vulnérabilité est critique.

        Returns
        -------
        bool: True si `score_danger` est supérieur ou égal à `seuil_critique`,
        False sinon.
        """
        return self.score_danger >= self.seuil_critique
