import ast
from collections import Counter
from pathlib import Path

from business_object.dépendance import Dependances
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
        extension (str): Extension du fichier, par exemple ".py"
            (déduite du chemin).
        liste_vulnerabilites (list[Vulnerabilite] | None): Vulnérabilités
            détectées, ou None tant que l'analyse n'a pas eu lieu.
        liste_dependances (list[Dependances] | None): Dépendances
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
        chemin: str,
        liste_vulnerabilites: list[Vulnerabilite] | None = None,
        liste_dependances: list[Dependances] | None = None,
        complexite: str | None = None,
        score: float | None = None,
        emissionCO2: float | None = None,
        AST_analyse: ast.Tree | None = None,
    ) -> None:
        self.id = id
        self.chemin = chemin
        self.extension = Path(chemin).suffix
        self.liste_vulnerabilites = liste_vulnerabilites
        self.liste_dependances = liste_dependances
        self.complexite = complexite
        self.score = score
        self.emissionCO2 = emissionCO2
        self.AST_analyse = AST_analyse

    def lire_contenu(self) -> str:
        """Retourne le contenu complet du fichier.
        Le fichier est lu en UTF-8.

        Returns:
            str: Le texte du fichier.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
            UnicodeDecodeError: Si le fichier n'est pas encodé en UTF-8.
        """
        with open(self.chemin, encoding=self.ENCODAGE) as f:
            return f.read()

    def lire_ligne(self, ligne_voulue: int) -> str:
        """Retourne une ligne précise du fichier.

        Le fichier est lu ligne par ligne, sans être chargé en entier
        en mémoire.

        Args:
            ligne_voulue (int): Numéro de la ligne, en commençant à 1.

        Returns:
            str: Le contenu de la ligne demandée, sans le saut de ligne
            final.

        Raises:
            ValueError: Si `ligne_voulue` est inférieur à 1.
            IndexError: Si `ligne_voulue` dépasse le nombre de lignes
                du fichier.
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
        """
        if ligne_voulue < 1:
            raise ValueError("ligne_voulue doit être supérieur ou égal à 1")
        with open(self.chemin, encoding=self.ENCODAGE) as f:
            for numero, ligne in enumerate(f, start=1):
                if numero == ligne_voulue:
                    return ligne.rstrip("\r\n")

        raise IndexError(
            f"La ligne {ligne_voulue} n'existe pas dans {self.nom}"
        )

    def obtenir_dependances_fichier(self) -> dict[str, int]:
        """Extrait les dépendances importées par le fichier.

        Le code est analysé avec le module `ast` : seuls les modules
        racines sont retenus (`import os.path` et `from os import path`
        comptent tous deux pour `os`). Les imports relatifs
        (`from . import x`) sont ignorés, car ils désignent le projet
        lui-même. Les fichiers qui ne sont pas du Python ne contiennent
        aucune dépendance détectable.

        Returns:
            dict[str, int]: Pour chaque module importé, son nombre
            d'occurrences. Dictionnaire vide si le fichier n'est pas
            un fichier Python ou n'importe rien.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
            SyntaxError: Si le code Python du fichier est invalide.

        Example:
            >>> # Pour un fichier contenant « import os » et « import os.path »
            >>> # fichier.obtenir_dependances_fichier()  ->  {"os": 2}
        """
        if self.extension != ".py":
            return {}

        arbre = ast.parse(self.lire_contenu(), filename=self.chemin)
        compteur: Counter[str] = Counter()

        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                for alias in noeud.names:
                    compteur[alias.name.split(".")[0]] += 1
            elif isinstance(noeud, ast.ImportFrom):
                if noeud.level == 0 and noeud.module:
                    compteur[noeud.module.split(".")[0]] += 1

        return dict(compteur)

    def est_a_risque(self) -> bool:
        """Indique si le fichier présente un risque.

        Un fichier est à risque s'il contient au moins une vulnérabilité
        critique.

        Returns:
            bool: True si au moins une vulnérabilité est critique,
            False sinon (y compris si la liste est vide).

        Raises:
            ValueError: Si le fichier n'a pas encore été analysé
                (`liste_vulnerabilites` vaut None).
        """
        if self.liste_vulnerabilites is None:
            raise ValueError(
                f"{self.nom} n'a pas encore été analysé : "
                "impossible d'évaluer le risque"
            )
        return any(v.est_critique() for v in self.liste_vulnerabilites)
