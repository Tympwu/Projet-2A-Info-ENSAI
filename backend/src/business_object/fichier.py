import ast
import sys
from pathlib import Path

from business_object.dependance import Dependances

from business_object.vulnerabilite import Vulnerabilite


class Fichier:
    """Représente un fichier source d'un dossier soumis à l'audit.

    Un fichier permet de lire son contenu (en entier ou ligne par ligne),
    d'en construire l'arbre syntaxique et d'en extraire les dépendances.
    Il stocke aussi les résultats de l'audit le concernant : vulnérabilités
    détectées, complexité, score et émissions de CO2 estimées.

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
        ECHELLE_COMPLEXITE (tuple[str, ...]): Complexités algorithmiques
        possibles, de la plus faible à la plus forte (l'ordre sert à
        comparer deux fichiers).
        AST_analyse (ast.Module | None): Arbre syntaxique du fichier,
            ou None tant qu'il n'a pas été construit.
    """

    ENCODAGE = "utf-8"

    ECHELLE_COMPLEXITE = (
        "O(1)", "O(n)", "O(n log n)", "O(n²)", "O(n² log n)",
        "O(n³)", "O(n^k), k > 3", "O(2^n)",
    )

    def __init__(
        self,
        id: int,
        chemin: str,
        liste_vulnerabilites: list[Vulnerabilite] | None = None,
        liste_dependances: list[Dependances] | None = None,
        complexite: str | None = None,
        score: float | None = None,
        emissionCO2: float | None = None,
        AST_analyse: ast.Module | None = None,
    ) -> None:
        """Initialise un fichier à auditer.

        Args:
            id (int): Identifiant unique du fichier.
            chemin (str): Chemin d'accès au fichier.
            liste_vulnerabilites (list[Vulnerabilite] | None): Vulnérabilités
                détectées. None signifie « pas encore analysé », alors
                qu'une liste vide signifie « analysé, rien trouvé ».
            liste_dependances (list[Dependances] | None): Dépendances
                détectées (même convention que pour les vulnérabilités).
            complexite (str | None): Niveau de complexité du code.
            score (float | None): Score du fichier.
            emissionCO2 (float | None): Émissions de CO2 estimées.
            AST_analyse (ast.Module | None): Arbre syntaxique déjà construit.
        """
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
                    return ligne.rstrip("\n")

        raise IndexError(
            f"La ligne {ligne_voulue} n'existe pas dans {self.chemin}"
        )

    def obtenir_ast(self) -> ast.Module:
        """Retourne l'arbre syntaxique du fichier, en le construisant si besoin.

        Returns:
            ast.Module: L'arbre syntaxique du fichier.

        Raises:
            ValueError: Si le fichier n'est pas un fichier Python.
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
            SyntaxError: Si le code Python du fichier est invalide.
        """
        if self.extension != ".py":
            raise ValueError(
                f"{self.chemin} n'est pas un fichier Python : "
                "pas d'arbre syntaxique"
            )
        if self.AST_analyse is None:
            self.AST_analyse = ast.parse(
                self.lire_contenu(), filename=self.chemin
            )
        return self.AST_analyse

    def obtenir_dependances_fichier(self) -> list[Dependances]:
        """Extrait les dépendances externes importées par le fichier.

        Returns:
            list[Dependances]: Dépendances externes, triées par nom.
            Liste vide si le fichier n'est pas Python ou n'importe rien
            d'externe.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
            SyntaxError: Si le code Python du fichier est invalide.
        """
        if self.extension != ".py":
            self.liste_dependances = []
            return self.liste_dependances  # Ecarter les fichiers non python

        noms: set[str] = set()
        for noeud in ast.walk(self.obtenir_ast()):  # ast.walk visite tous les noeuds
            if isinstance(noeud, ast.Import):
                noms.update(alias.name.split(".")[0] for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom):
                if noeud.level == 0 and noeud.module:
                    noms.add(noeud.module.split(".")[0])

        externes = sorted(noms - sys.stdlib_module_names)
        self.liste_dependances = [
            Dependances(nom=nom, auteur=None, version=None)
            for nom in externes
        ]
        return self.liste_dependances

    def est_a_risque(self) -> bool:
        """Indique si le fichier présente un risque.

        Returns:
            bool: True si au moins une vulnérabilité est critique,
            False sinon (y compris si la liste est vide).

        Raises:
            ValueError: Si le fichier n'a pas encore été analysé
                (`liste_vulnerabilites` vaut None).
        """
        if self.liste_vulnerabilites is None:
            raise ValueError(
                f"{self.chemin} n'a pas encore été analysé : "
                "impossible d'évaluer le risque"
            )
        return any(v.est_critique() for v in self.liste_vulnerabilites)
