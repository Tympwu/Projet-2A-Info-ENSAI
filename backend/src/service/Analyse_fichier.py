import ast
import os

from dotenv import load_dotenv

from business_object.fichier import Fichier


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
        # On donne d'abord une valeur par défaut, puis on charge la configuration.
        # Donc l'attribut existe toujours, même si le chargement ne trouve rien.
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

        # os.getenv(nom, défaut) renvoie le défaut si la variable n'existe pas :
        # pas d'erreur, pas de plantage au démarrage.
        self.api_url_OSV = os.getenv("OSV_API_URL", self.URL_OSV_PAR_DEFAUT)

        # Pour l'instant, on met pas  consommation_estimee_kWh et emissionCO2e.
        # C'est des résultats propres à chaque fichier (Fichier.emissionCO2 existe déjà),
        # donc ils ne doivent pas être stockés ici. Les coefficients de configuration nécessaires
        # au calcul du CO2 seront ajoutés ici plus tard, quand on saura quel calcul faire

    NOEUDS_DECISION = (
        ast.If,
        ast.IfExp,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
    )

    def analyser_complexite_code(self, fichier: Fichier) -> str | None:
        """
        Calcule la complexité cyclomatique d'un fichier Python.

        La complexité cyclomatique compte le nombre de chemins d'exécution
        indépendants : elle vaut 1 pour un code sans aucune branche, puis
        augmente de 1 à chaque condition, boucle, gestionnaire d'exception,
        opérateur `and` / `or` ou clause de compréhension de liste.
        Le résultat est écrit dans `fichier.complexite` et retourné.

        Paramètres
        ----------
        fichier (Fichier): Fichier à analyser.

        Returns
        -------
        str | None: Complexité sous forme de texte (par exemple "7"), ou None
        si le fichier n'est pas analysable (autre langage que Python, syntaxe
        invalide ou encodage illisible).
        """
        # complexité cyclomatique : mesure standard de complexité d'un code, donc
        # plus simple à expliquer et à calculer.

        resultat: str | None = None

        # `ast` ne sait lire que du Python : pour tout autre type de fichier,
        # la mesure n'a pas de sens, on laisse la complexité à None.
        if fichier.extension.lower() == ".py":
            try:
                # On réutilise la lecture déjà écrite dans l'objet métier
                # plutôt que d'ouvrir le fichier une deuxième fois ici.
                arbre = ast.parse(fichier.lire_contenu())
                resultat = str(1 + self._compter_points_de_decision(arbre))
            except (SyntaxError, UnicodeDecodeError):
                # Un fichier soumis peut contenir du code invalide : ce n'est
                # pas une erreur du programme, juste un fichier non analysable.

                resultat = None

        # Le Service remplit le business object et Audit lira ensuite fichier.complexite
        fichier.complexite = resultat
        return resultat

    @staticmethod
    def _compter_points_de_decision(arbre: ast.AST) -> int:
        """
        Compte les points de décision d'un arbre syntaxique.

        Paramètres
        ----------
        arbre (ast.AST): Arbre syntaxique d'un fichier Python.

        Returns
        -------
        int: Nombre de points de décision (conditions, boucles, exceptions,
        opérateurs and/or, clauses de compréhension).
        """
        total = 0
        # ast.walk parcourt tous les nœuds de l'arbre, y compris ceux qui sont
        # imbriqués dans des fonctions ou des classes.
        for noeud in ast.walk(arbre):
            if isinstance(noeud, Analyse_fichier.NOEUDS_DECISION):
                total += 1
            elif isinstance(noeud, ast.BoolOp):
                # `a and b and c` contient 2 opérateurs, donc 2 chemins en plus.
                total += len(noeud.values) - 1
            elif isinstance(noeud, ast.comprehension):
                # `for x in liste if cond` : 1 boucle + 1 par condition.
                total += 1 + len(noeud.ifs)
        return total


"""
class ComplexityAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.loop_depth = 0
        self.total_operations = 0
        self.has_nested_loops = False
        self.max_nesting = 0
        
    def visit_For(self, node):
        # Incrémenter la profondeur de boucle
        self.loop_depth += 1
        self.max_nesting = max(self.max_nesting, self.loop_depth)
        
        # Analyser le corps de la boucle
        self.generic_visit(node)
        
        # Décrémenter après analyse
        self.loop_depth -= 1
        
    def visit_While(self, node):
        self.loop_depth += 1
        self.max_nesting = max(self.max_nesting, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1
        
    def visit_Call(self, node):
        # Compter chaque appel comme une opération (simplification)
        self.total_operations += 1
        self.generic_visit(node)
        
    def visit_BinOp(self, node):
        # Compter les opérations binaires (+, -, *, /)
        self.total_operations += 1
        self.generic_visit(node)

def analyze_complexity(source_code):
    tree = ast.parse(source_code)
    analyzer = ComplexityAnalyzer()
    analyzer.visit(tree)
"""
