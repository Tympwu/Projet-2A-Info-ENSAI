class vulnerabilites:
    """
    Représente une vulnérabilité de sécurité détectée dans un projet.

    Une vulnérabilité est décrite par un texte et un score de danger.
    Au-delà d'un seuil,(à voir lequel je ne sais) elle est considérée comme critique.

    Attributes
    ---------
    seuil_critique (int): Score à partir duquel une vulnérabilité est jugée critique.
        description (str): Description de la vulnérabilité.
        score_danger (int): Score de danger, compris entre 0 et 10.
    """

    seuil_critique = 9.0

    def __init__(self, description: str, score_danger: int) -> None:
        """
        Initialise une vulnérabilité.

        Paramètres
        ----------
            description (str): Description de la vulnérabilité.
            score_danger (int): Score de danger, entre 0 et 10 inclus.

        Returns
        ---------
        None
        """
        self.description = description
        self.score_danger = score_danger

    def est_critique(self) -> bool:
        """
        Indique si la vulnérabilité est critique.

        Returns
        ---------
            bool: True si `score_danger` est supérieur ou égal à
            `SEUIL_CRITIQUE`, False sinon.
        """
        return self.score_danger >= self.seuil_critique
