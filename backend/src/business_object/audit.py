from datetime import datetime

from business_object.dossier import Dossier
from business_object.fichier import Fichier


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
    statut (str): État de l'audit ("créé", "échoué", "validé", "refusé").
    score (float | None): Score global (None tant qu'il n'est pas calculé).
    emissionCO2_total (float | None): Émissions de CO2 totales (None avant le lancement).
    dossier (Dossier): Dossier audité.
    """

    def __init__(
        self,
        id: int,
        dossier: Dossier,
        score: int | None = None,
        emissionCO2_total: float | None = None,
        date: datetime = None,
        statut: str = "créé",
    ) -> None:
        """
        Initialise un audit.

        Parameters
        ----------
        id (int): Identifiant unique de l'audit.
        dossier (Dossier): Dossier à auditer.
        score (int | None): Score de l'audit (par défaut : None).
        emissionCO2_total (float | None): emission de CO2 cumulé de l'audit (par défaut : None)
        date (datetime | None): Date de l'audit (par défaut : maintenant).
        statut (str): Statut initial (par défaut : "créé"). Peut valoir "créé", "échoué", "validé", "refusé"

        """
        self.id = id
        self.date = date or datetime.now()
        self.statut = statut
        self.score = score
        self.emissionCO2_total = emissionCO2_total
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
                "Impossible de calculer le score : le dossier ne contient aucun fichier."
            )
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
        rangs = [
            Fichier.ECHELLE_COMPLEXITE.index(c) + 1 for c in self.obtenir_complexites().values()
        ]
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
        Exécute l'audit du dossier.

        Calcule le score global du dossier à partir des scores de ses fichiers,
     puis détermine si l'audit est validé ou refusé.

        Un audit est :
        - "validé" si le score global est strictement inférieur à 5.
        - "refusé" si le score global est supérieur ou égal à 5.
        - "échoué" si une erreur empêche le calcul du score.

    Les émissions de CO2 totales sont également calculées si tous les
    fichiers possèdent une valeur d'émission.

    Returns
    -------
    bool:
        True si l'audit a été correctement exécuté, qu'il soit validé
        ou refusé.

    Raises
    ------
    ValueError:
        Si le dossier ne contient aucun fichier, si certains scores
        ne sont pas calculés ou si certaines émissions de CO2 sont
        indisponibles.
    """

        try:
            fichiers = self.dossier.obtenir_fichiers()

            self.calculer_score()

            if self.score < 5:
                self.statut = "validé"
            else:
                self.statut = "refusé"

            if any(f.emissionCO2 is None for f in fichiers):
                raise ValueError(
                    "Impossible de calculer les émissions totales : "
                    "les émissions de certains fichiers ne sont pas calculées."
                )

            self.emissionCO2_total = sum(
                f.emissionCO2 for f in fichiers
            )

            return True

        except ValueError:
            self.statut = "échoué"
            raise

    def __repr__(self) -> str:
        """
        Représentation str de l'audit
        """
        return (
            f"Audit(id={self.id}, date={self.date:%d/%m/%Y}, statut={self.statut}, "
            f"score={self.score}, emissionCO2_total={self.emissionCO2_total})"
        )
