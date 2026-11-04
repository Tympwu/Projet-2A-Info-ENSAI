import ast
import os

from dotenv import load_dotenv

from business_object.fichier import Fichier


class AnalyseurComplexite(ast.NodeVisitor):
    """
    Mesure l'imbrication des boucles `for` et `while` d'un arbre syntaxique Python.

    On crée un analyseur par fichier : ses compteurs sont propres à ce fichier. Python appelle
    automatiquement `visit_For` et `visit_While` quand il rencontre ces types de nœuds.Du code
    placé dans `d` boucles imbriquées s'exécute environ n^d fois.
    La complexité estimée est donc la profondeur maximale d'imbrication.

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
    LIBELLES_PAR_PROFONDEUR (dict[int, str]): Complexité associée à chaque profondeur de boucles.
    LIBELLE_AU_DELA (str): Complexité utilisée au-delà de trois boucles imbriquées.
    api_url_OSV (str): Adresse de l'API OSV utilisée pour chercher les vulnérabilités.
    """

    URL_OSV_PAR_DEFAUT = "https://api.osv.dev/v1/query"

    # Libellés produits par l'estimation. Ils doivent tous exister dans
    # Fichier.ECHELLE_COMPLEXITE (vérifié dans _libelle).
    LIBELLES_PAR_PROFONDEUR = {
        0: "O(1)",
        1: "O(n)",
        2: "O(n²)",
        3: "O(n³)",
    }
    LIBELLE_AU_DELA = "O(n^k), k > 3"

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

        # Pour l'instant, on met pas  consommation_estimee_kWh et emissionCO2e.
        # C'est des résultats propres à chaque fichier (Fichier.emissionCO2 existe déjà),
        # donc ils ne doivent pas être stockés ici. Les coefficients de configuration nécessaires
        # au calcul du CO2 seront ajoutés ici plus tard, quand on saura quel calcul faire

    def analyser_complexite_code(self, fichier: Fichier) -> str | None:
        """
        Estime la complexité algorithmique d'un fichier Python.

        L'estimation est une heuristique simple : elle lit le code sans l'exécuter
        et retient la profondeur maximale d'imbrication des boucles `for` et
        `while` (aucune boucle : O(1), une : O(n), deux imbriquées : O(n²)...).
        Le résultat est écrit dans `fichier.complexite` et retourné.

        Seules les boucles `for` et `while` sont comptées.

        Paramètres
        ----------
        fichier (Fichier): Fichier à analyser.

        Returns
        -------
        str | None: Une valeur de `Fichier.ECHELLE_COMPLEXITE` (par exemple
        "O(n²)"), ou None si le fichier n'est pas analysable (autre langage que
        Python, syntaxe invalide ou encodage illisible).

        Raises
        ------
        FileNotFoundError: Si le fichier n'existe pas au chemin indiqué.
        ValueError: Si un libellé produit par l'estimation n'est pas dans
        `Fichier.ECHELLE_COMPLEXITE` (erreur de configuration à corriger).
        """

        resultat: str | None = None

        # Fichier.obtenir_ast() construit l'arbre une seule fois et le garde dans
        # fichier.AST_analyse : les autres analyses (anti-patterns...) le réutilisent.
        try:
            arbre = fichier.obtenir_ast()
        except (ValueError, SyntaxError, UnicodeDecodeError):
            arbre = None

        if arbre is not None:
            # Un nouvel analyseur par fichier
            analyseur = AnalyseurComplexite()
            analyseur.visit(arbre)
            resultat = self._libelle(analyseur)

        # Le Service remplit le business object et Audit lira ensuite fichier.complexite
        fichier.complexite = resultat
        return resultat

    def _libelle(self, analyseur: AnalyseurComplexite) -> str:
        """
        Convertit la profondeur de boucles mesurée en libellé de l'échelle.

        Paramètres
        ----------
        analyseur (AnalyseurComplexite): Analyseur qui a déjà parcouru le fichier.

        Returns
        -------
        str: Libellé de la complexité (valeur de Fichier.ECHELLE_COMPLEXITE).

        Raises
        ------
        ValueError: Si le libellé n'existe pas dans Fichier.ECHELLE_COMPLEXITE.
        """
        libelle = self.LIBELLES_PAR_PROFONDEUR.get(analyseur.max_imbrication, self.LIBELLE_AU_DELA)

        if libelle not in Fichier.ECHELLE_COMPLEXITE:
            raise ValueError(f"Libellé de complexité absent de l'échelle de Fichier : {libelle!r}")
        return libelle
