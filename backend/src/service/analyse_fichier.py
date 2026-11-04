import ast
import os

from dotenv import load_dotenv

from business_object.fichier import Fichier


class AnalyseurComplexite(ast.NodeVisitor):
    """
    Mesure l'imbrication des boucles `for` et `while` d'un arbre syntaxique Python.

    On crée un analyseur par fichier. Python appelle automatiquement `visit_For` et `visit_While` 
    quand il rencontre ces types de nœuds.

    Attributs
    ---------
    profondeur (int): Nombre de boucles qui enveloppent le nœud en cours de visite.
    max_imbrication (int): Profondeur maximale de boucles imbriquées dans le fichier (résultat).
    boucles_imbriquees (bool): True si le fichier contient au moins deux boucles imbriquées.
    """

    def __init__(self) -> None:
        """
        Initialise un analyseur vierge.

        Returns
        -------
        None
        """
        self.profondeur: int = 0
        self.max_imbrication: int = 0
        # Cette information servira aussi à detecter_anti_patterns : un seul
        # parcours de l'arbre suffit pour la complexité et les boucles imbriquées.
        self.boucles_imbriquees: bool = False

    def _visiter_boucle(self, noeud: ast.AST) -> None:
        """
        Visite une boucle `for` ou `while` : son corps est répété environ n fois.

        Paramètres
        ----------
        noeud (ast.For | ast.While): Nœud de la boucle.

        Returns
        -------
        None
        """

        self.profondeur += 1
        self.max_imbrication = max(self.max_imbrication, self.profondeur)
        if self.profondeur >= 2:
            self.boucles_imbriquees = True

        for instruction in noeud.body:
            self.visit(instruction)

        self.profondeur -= 1

        for instruction in noeud.orelse:
            self.visit(instruction)

    visit_For = _visiter_boucle
    visit_While = _visiter_boucle


class Analyse_fichier:
    """
    Analyse les fichiers d'un dossier (complexité, dépendances, vulnérabilités...).

    Cette classe ne garde aucun résultat d'analyse : elle ne conserve que la
    configuration, commune à tous les fichiers. Une seule instance peut donc
    analyser autant de fichiers que l'on veut ; chaque méthode reçoit le fichier
    concerné et écrit son résultat dans cet objet Fichier.

    Attributs
    ---------
    URL_OSV_PAR_DEFAUT (str): Adresse de l'API OSV utilisée si aucune n'est configurée.
    (Valeur de secours : l'application fonctionne même si aucune configuration n'est fournie)
    api_url_OSV (str): Adresse de l'API OSV utilisée pour chercher les vulnérabilités.
    """

    URL_OSV_PAR_DEFAUT = "https://api.osv.dev/v1/query"

    def __init__(self) -> None:
        """
        Initialise l'analyseur et charge sa configuration.

        Returns
        -------
        None
        """
        self.api_url_OSV: str = self.URL_OSV_PAR_DEFAUT
        self.load_environment_variables()

    def load_environment_variables(self) -> None:
        """
        Charge la configuration depuis les variables d'environnement.

        Lit d'abord le fichier `.env` s'il existe (il alimente les variables
        d'environnement), puis lit la variable OSV_API_URL. Si elle est absente,
        `api_url_OSV` garde sa valeur par défaut.

        Returns
        -------
        None
        """

        load_dotenv()

        self.api_url_OSV = os.getenv("OSV_API_URL", self.URL_OSV_PAR_DEFAUT)

    def analyser_complexite_code(self, fichier: Fichier) -> int | None:
        """
        Estime la complexité algorithmique d'un fichier Python.

        L'estimation retient la profondeur maximale d'imbrication des boucles `for` et
        `while`. Cette profondeur est l'exposant k de la complexité O(n^k)
        Le résultat est écrit dans `fichier.complexite` et retourné.

        Paramètres
        ----------
        fichier (Fichier): Fichier à analyser.

        Returns
        -------
        int | None: L'exposant k de la complexité estimée O(n^k), ou None si le fichier
        n'est pas analysable

        Raises
        ------
        FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
        """

        resultat: int | None = None

        try:
            arbre = fichier.obtenir_ast()
        except (ValueError, SyntaxError, UnicodeDecodeError):
            arbre = None

        if arbre is not None:
            # Un nouvel analyseur par fichier
            analyseur = AnalyseurComplexite()
            analyseur.visit(arbre)
            resultat = analyseur.max_imbrication

        fichier.complexite = resultat
        return resultat
