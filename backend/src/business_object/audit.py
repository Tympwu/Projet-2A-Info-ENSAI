
from datetime import datetime

from business_object.dossier import Dossier

from .fichier import Fichier


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
        Donne la pire complexité algorithmique des fichiers du dossier, sous forme de rang.

        Le rang est la position dans `Fichier.ECHELLE_COMPLEXITE`, à partir de 1, ce qui
        permet de comparer simplement (plus le rang est grand, plus c'est coûteux).

        Returns
        -------
        int: Rang de la pire complexité (1 = O(1), 2 = O(n), 3 = O(n log n)...),
        ou 0 si aucun fichier n'a de complexité exploitable.
        """
        rangs = [Fichier.ECHELLE_COMPLEXITE.index(c) + 1
                 for c in self.obtenir_complexites().values()]
        return max(rangs, default=0)

    def obtenir_complexites(self) -> dict[int, str]:
        """
        Donne la complexité de chaque fichier, dans un format facile à réutiliser.

        Complète `calculer_complexite()` et permet de repérer les fichiers les plus coûteux.

        Returns
        -------
        dict[int, str]: Complexité de chaque fichier, sous la forme
        {id du fichier: "O(n²)"}. Les fichiers sans complexité reconnue
        (None ou valeur hors échelle) sont absents.
        """
        return {
            f.id: f.complexite
            for f in self.dossier.obtenir_fichiers()
            if f.complexite in Fichier.ECHELLE_COMPLEXITE
        }

    def lancer(self) -> bool:
        """
        Exécute l'audit.

        Calcule le score global et les émissions de CO2 totales. Si tout se
        passe bien, le statut passe à True et la méthode retourne True. Si le
        score ne peut pas être calculé, le statut passe à False et l'erreur
        est relancée à l'appelant, qui doit la gérer.

        Returns
        -------
        bool: True si l'audit s'est terminé correctement. La méthode ne
        retourne jamais False : en cas d'échec, elle lève une exception.

        Raises
        ------
        ValueError: Si le score global ne peut pas être calculé (dossier vide
        ou score d'un fichier non calculé, voir `calculer_score`).
        """
        try:
            self.calculer_score()
        except ValueError:
            self.statut = False
            raise
        self.emissionCO2_total = sum(
            f.emissionCO2 for f in self.dossier.obtenir_fichiers()
            if f.emissionCO2 is not None
        )
        self.statut = True
        return True

    def __repr__(self) -> str:
        """
        Représentation str de l'audit
        """
        return (
            f"Audit(id={self.id}, date={self.date:%d/%m/%Y}, statut={self.statut}, "
            f"score={self.score}, emissionCO2_total={self.emissionCO2_total})"
        )
