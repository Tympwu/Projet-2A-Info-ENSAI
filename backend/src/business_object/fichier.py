import ast
import re
import sys
import tomllib
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
        complexite (int | None): exposant k du niveau de complexité O(n^k)
        score (float | None): Score du fichier, ou None avant analyse.
        emissionCO2 (float | None): Émissions de CO2 estimées, ou None
            avant analyse.
        AST_analyse (ast.Module | None): Arbre syntaxique du fichier,
            ou None tant qu'il n'a pas été construit.
    """

    ENCODAGE = "utf-8"

    MOTIF_EXIGENCE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(.*)$")

    MOTIF_VERSION_EXACTE = re.compile(r"(?<![<>!~=])===?\s*([^\s,;]+)")
    # utile pour extraire les versions

    def __init__(
        self,
        chemin: str,
        id: int | None = None,
        extension: str | None = None,
        liste_vulnerabilites: list[Vulnerabilite] | None = None,
        liste_dependances: list[Dependances] | None = None,
        complexite: int | None = None,
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
            complexite (int | None): Niveau de complexité du code.
            score (float | None): Score du fichier.
            emissionCO2 (float | None): Émissions de CO2 estimées.
            AST_analyse (ast.Module | None): Arbre syntaxique déjà construit.
        """
        self.id = id
        self.chemin = chemin
        self.extension = extension if extension else Path(chemin).suffix
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

        raise IndexError(f"La ligne {ligne_voulue} n'existe pas dans {self.chemin}")

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
            raise ValueError(f"{self.chemin} n'est pas un fichier Python : pas d'arbre syntaxique")
        if self.AST_analyse is None:
            self.AST_analyse = ast.parse(self.lire_contenu(), filename=self.chemin)
        return self.AST_analyse

    def obtenir_dependances_fichier(self) -> list[Dependances]:
        """
        Retourne les dépendances du fichier, en les extrayant au premier appel.

        Si `liste_dependances` est déjà remplie (par un appel précédent à
        `extraire_dependances`), elle est retournée telle quelle, sans être
        recalculée ni écrasée.

        Returns:
            list[Dependances]: Dépendances du fichier. Liste vide si le fichier
            n'est pas d'un type pris en charge, n'est pas lisible ou ne déclare
            rien d'externe.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué (et
                que les dépendances n'avaient pas encore été extraites).
        """

        if self.liste_dependances is None:
            self.extraire_dependances()
        return self.liste_dependances or []

    def extraire_dependances(self) -> bool:
        """Extrait les dépendances déclarées par le fichier et les range dans `liste_dependances`.

        Trois types de fichiers sont pris en charge :
        - un fichier Python (`.py`) : modules importés qui ne font pas partie de la
          bibliothèque standard (version inconnue, donc None) ;
        - un fichier `requirements.txt` (ou `requirements-dev.txt`...) : une dépendance
          par ligne ;
        - un fichier `pyproject.toml` : la liste `dependencies` de la section `[project]`.

        Une version n'est retenue que si elle est épinglée avec `==` (par exemple
        `requests==2.31.0`). Avec `>=2.0`, la version installée est inconnue : None.

        Returns:
            bool: True si les dépendances ont pu être extraites (la liste peut être vide),
            False si le fichier n'est pas d'un type pris en charge ou n'est pas lisible
            (`liste_dependances` vaut alors None).

        Raises:
            FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
        """
        nom_fichier = Path(self.chemin).name.lower()
        dependances: list[Dependances] | None = None

        try:
            if self.extension == ".py":
                # Un import ne contient pas de version : elle vaut None.
                noms: set[str] = set()
                for noeud in ast.walk(self.obtenir_ast()):  # ast.walk visite tous les noeuds
                    if isinstance(noeud, ast.Import):
                        noms.update(alias.name.split(".")[0] for alias in noeud.names)
                    elif isinstance(noeud, ast.ImportFrom):
                        if noeud.level == 0 and noeud.module:
                            noms.add(noeud.module.split(".")[0])
                externes = sorted(noms - sys.stdlib_module_names)
                dependances = [Dependances(nom=nom, auteur=None, version=None) for nom in externes]
            elif nom_fichier.startswith("requirements") and nom_fichier.endswith(".txt"):
                dependances = self._lire_exigences(self.lire_contenu().splitlines())
            elif nom_fichier == "pyproject.toml":
                donnees = tomllib.loads(self.lire_contenu())
                dependances = self._lire_exigences(donnees.get("project", {}).get(
                    "dependencies", []))
        except (SyntaxError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            dependances = None
        self.liste_dependances = dependances
        return dependances is not None

    def _lire_exigences(self, lignes: list[str]) -> list[Dependances]:
        """
        Convertit des lignes comme `requests[security]==2.31.0` en dépendances.
        Cete methode permet de lire correctement les dépendances

        Les lignes vides, les commentaires, les options (`-r autre.txt`), les chemins
        locaux et les adresses directes (`git+https://...`) sont ignorés.

        Args:
            lignes (list[str]): Lignes d'un `requirements.txt`, ou entrées de la liste
                `dependencies` d'un `pyproject.toml`.

        Returns:
            list[Dependances]: Dépendances triées par nom, sans doublon (même nom
            et même version).
        """
        uniques: dict[tuple[str, str | None], Dependances] = {}
        for ligne in lignes:
            ligne = re.split(r"\s#", ligne, maxsplit=1)[0].split(";", 1)[0].strip()
            if not ligne or ligne.startswith(("#", "-", ".", "/")):
                continue

            correspondance = self.MOTIF_EXIGENCE.match(ligne)
            if correspondance is None:
                continue
            nom, reste = correspondance.groups()

            if "://" in ligne and not reste.lstrip().startswith("@"):
                continue

            epinglee = self.MOTIF_VERSION_EXACTE.search(reste)
            version = epinglee.group(1) if epinglee and "*" not in epinglee.group(1) else None
            uniques[(nom.lower(), version)] = Dependances(nom=nom, auteur=None, version=version)

        return [uniques[cle] for cle in sorted(uniques, key=lambda c: (c[0], c[1] or ""))]

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
                f"{self.chemin} n'a pas encore été analysé : impossible d'évaluer le risque"
            )
        return any(v.est_critique() for v in self.liste_vulnerabilites)

    @staticmethod
    def formater_complexite(k: int | None) -> str | None:
        """Écrit l'exposant d'une complexité sous la forme O(n^k), pour l'affichage.

        Args:
            k (int | None): Exposant de la complexité (0, 1, 2...), ou None.

        Returns:
            str | None: "O(1)" pour 0, "O(n)" pour 1, "O(n^k)" au-delà
            (par exemple "O(n^2)"), ou None si `k` vaut None.
        """
        if k is None:
            return None
        if k == 0:
            return "O(1)"
        if k == 1:
            return "O(n)"
        return f"O(n^{k})"
