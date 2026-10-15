
from datetime import datetime

from business_object.dossier import Dossier


class Audit:
    """
    Représente l'audit d'un dossier après son analyse.

    L'audit ne fait pas l'analyse des fichiers : les scores, complexités et
    émissions de chaque fichier sont calculés par la couche Service. L'audit se
    contente de les agréger pour obtenir les résultats globaux.

    Attributs
    ---------
    id (int): Identifiant unique de l'audit.
    date (datetime): Date et heure de création de l'audit.
    statut (str): État de l'audit ("créé", "en cours", "terminé" ou "échoué").
    score (float | None): Score global (None tant qu'il n'est pas calculé).
    emissionCO2_total (float | None): Émissions de CO2 totales (None avant le lancement).
    dossier (Dossier): Dossier audité.
    """

    def __init__(self, id: int, dossier: Dossier,
                 date: datetime = None, statut: str = "créé") -> None:
        """
        Initialise un audit.

        Parameters
        ----------
        id (int): Identifiant unique de l'audit.
        dossier (Dossier): Dossier à auditer.
        date (datetime | None): Date de l'audit (par défaut : maintenant).
        statut (str): Statut initial (par défaut : "créé").

        """
        self.id = id
        self.date = date or datetime.now()
        self.statut = statut
        self.score = None
        self.emissionCO2_total = None
        self.dossier = dossier

    def calculer_score(self) -> float:
        """
        Calcule le score global de l'audit et le stocke dans `self.score`.

        Le score global est la moyenne des scores des fichiers du dossier.
        Ces scores doivent avoir été calculés au préalable par la couche Service pour chaque fichier

        Returns
        -------
        float: Score global (moyenne des scores des fichiers).

        Raises
        ------
        ValueError: Si le dossier n'a aucun fichier, ou si le score d'un fichier
        n'a pas encore été calculé, ça évite d'avoir un score = 0 qui fausserait la moyenne
        """
        fichiers = self.dossier.obtenir_fichiers()
        if not fichiers:
            raise ValueError(
                "Impossible de calculer le score : le dossier ne contient aucun fichier.")
        if any(f.score is None for f in fichiers):
            raise ValueError(
                "Impossible de calculer le score : le score de certains fichiers n'est pas calculé."
                )
        self.score = sum(f.score for f in fichiers) / len(fichiers)
        return self.score

    def calculer_complexite(self) -> int:
        """
        Calcule la complexité moyenne des fichiers du dossier.

        Seules les complexités numériques sont prises en compte ; celles qui
        sont absentes ou non convertibles en nombre sont ignorées.

        Returns
        -------
        int: Complexité moyenne arrondie à l'entier le plus proche
        (0 si aucun fichier n'a de complexité exploitable).
        """
        valeurs = list(self.obtenir_complexites().values())
        if not valeurs:
            return 0
        return round(sum(valeurs) / len(valeurs))

    def obtenir_complexites(self) -> dict[int, float]:
        """
        Donne la complexité de chaque fichier (dans un format facile à réutiliser ?)

        Complète `calculer_complexite()` : la moyenne résume, le fait de détailler permet
         de repérer les fichiers les plus complexes.

        Returns
        -------
        dict[int, float]: Complexité de chaque fichier, sous la forme
        {id du fichier: complexité}. Les fichiers sans complexité numérique
        sont absents.
        """
        complexites: dict[int, float] = {}
        for f in self.dossier.obtenir_fichiers():
            if f.complexite is not None:
                try:
                    complexites[f.id] = float(f.complexite)
                except ValueError:
                    pass
        return complexites

    def lancer(self) -> bool:
        """
        Exécute l'audit.

        Calcule le score global et les émissions de CO2 totales. Le statut passe
        à True si l'audit s'est terminé correctement, et reste False si le
        calcul a échoué.

        Returns
        -------
        bool: True si l'audit est réalisé, False si le calcul a échoué.
        """
        self.statut = False
        try:
            self.calculer_score()
        except ValueError:
            return False
        self.emissionCO2_total = sum(
            f.emissionCO2 for f in self.dossier.obtenir_fichiers()
            if f.emissionCO2 is not None
        )
        self.statut = True
        return True
