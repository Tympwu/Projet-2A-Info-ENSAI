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
    statut (str): État de l'audit ("créé", "échoué", "validé", "refusé").
    score (float | None): Score global (None tant qu'il n'est pas calculé).
    emissionCO2_total (float | None): Émissions de CO2 totales (None avant le lancement).
    dossier (Dossier): Dossier audité.
    """

    def __init__(
        self,
        dossier: Dossier,
        id: int | None = None,
        score: float | None = None,
        emissionCO2_total: float | None = None,
        complexite_total: int | None = None,
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
        statut (str): Statut initial (par défaut : "créé"). Peut valoir "créé", "échoué", "validé",
        "refusé"

        """
        self.id = id
        self.date = date or datetime.now()
        self.statut = statut
        self.score = score
        self.emissionCO2_total = emissionCO2_total
        self.dossier = dossier
        self.complexite_total = complexite_total

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
        self.score = max(f.score for f in fichiers)
        return self.score

    def calculer_complexite(self) -> int | None:
        """
        Calcul la pire complexité des fichiers du dossier et l'enregistre localement, sous forme de l'exposant k.

        Returns
        -------
        int | None: Le plus grand exposant k (0 pour O(1), 1 pour O(n), 2 pour O(n^2)...),
        ou None si aucun fichier n'a de complexité exploitable.
        """
        self.complexite_total = max(self.obtenir_complexites().values(), default=None)
        return self.complexite_total

    def obtenir_complexites(self) -> dict[int, int]:
        """
        Donne la complexité de chaque fichier, dans un format facile à réutiliser.

        Returns
        -------
        dict[int, int]: {id du fichier: exposant k}. Les fichiers sans complexité
        (None) sont absents.
        """
        return {
            f.id: f.complexite for f in self.dossier.obtenir_fichiers() if f.complexite is not None
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
        self.score = None
        self.emissionCO2_total = None
        try:
            self.complexite_total = self.calculer_complexite()

            fichiers = self.dossier.obtenir_fichiers()

            self.calculer_score()

            if any(f.emissionCO2 is None for f in fichiers if f.extension == ".py"):
                raise ValueError(
                    "Impossible de calculer les émissions totales : "
                    "les émissions de certains fichiers ne sont pas calculées."
                )

            self.emissionCO2_total = sum(
                (f.emissionCO2 for f in fichiers if f.extension == ".py"), start=0
            )

            self.score = (10 - round(self.emissionCO2_total / 0.01)) + (10 - self.score)

            if self.score > 15:
                self.statut = "validé"
            else:
                self.statut = "refusé"

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
