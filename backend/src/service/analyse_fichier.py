
import ast
import os
import timeit

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
        #generic_visit() pour déléguer à NodeVisitor le parcours récursif de l'ensemble des sous-nœuds d'une boucle
        #visite automatiquement tous les sous-nœuds du nœud courant.
        self.generic_visit(noeud)

        self.profondeur -= 1

        """for instruction in noeud.body:
            self.visit(instruction)

        self.profondeur -= 1

        for instruction in noeud.orelse:
            self.visit(instruction)"""

    visit_For = _visiter_boucle
    visit_While = _visiter_boucle

class AnalyseurAntiPatterns(ast.NodeVisitor):
    """
    il détecte quelques pratiques potentiellement énergivores dans un code Python.

    Pour le moment, on recherche :
    - Les boucles imbriquées (une boucle dans une autre).
    - La récursivité directe (une fonction qui s'appelle elle-même).
    """

    def __init__(self) -> None:
        # pour compter combien de boucles sont imbriquées.
        self.profondeur = 0
        # Passe à True dès qu'on trouve une boucle dans une autre boucle.
        self.boucles_imbriquees = False
        # Garde le nom des fonctions qu'on est en train d'analyser.
        self.fonctions = []
        # Contient les noms des fonctions pour lesquelles on a trouvé
        # un appel récursif.
        self.fonctions_recursives = set()
    def _visiter_boucle(self, noeud: ast.AST) -> None:
        # On entre dans une boucle : on augmente la profondeur de 1.
        self.profondeur += 1
        # Si la profondeur atteint 2, cela signifie qu'une boucle
        # se trouve à l'intérieur d'une autre boucle.
        if self.profondeur >= 2:
            self.boucles_imbriquees = True
        try:
            # On demande à Python de parcourir automatiquement
            # toutes les instructions contenues dans cette boucle.
            self.generic_visit(noeud)
        finally:
            # On sort de la boucle : on revient au niveau précédent.
            self.profondeur -= 1

    # Ces deux méthodes utilisent le même traitement :
    # on surveille les boucles for et les boucles while.
    visit_For = _visiter_boucle
    visit_While = _visiter_boucle

    def visit_FunctionDef(self, noeud: ast.FunctionDef) -> None:
        # On analyse aussi les décorateurs et les valeurs par défaut
        # des paramètres de la fonction.
        for decorateur in noeud.decorator_list:
            self.visit(decorateur)
        for argument in noeud.args.defaults:
            self.visit(argument)
        for argument in noeud.args.kw_defaults:
            if argument is not None:
                self.visit(argument)

        # On mémorise le nom de la fonction qu'on est en train de visiter.
        self.fonctions.append(noeud.name)
        try:
            # On parcourt les instructions de cette fonction.
            for instruction in noeud.body:
                self.visit(instruction)
        finally:
            # On a terminé cette fonction : on la retire de la liste.
            self.fonctions.pop()

    # Même traitement pour les fonctions asynchrones.
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, noeud: ast.Call) -> None:
        # On vérifie les appels uniquement si on se trouve dans une fonction.
        if self.fonctions:

            # Nom de la fonction actuellement analysée.
            nom_fonction = self.fonctions[-1]

            # Cas 1 : appel direct, par exemple :
            # def calculer():
            #     calculer()
            appel_recursif = (
                isinstance(noeud.func, ast.Name)
                and noeud.func.id == nom_fonction
            )

            # Cas 2 : appel d'une méthode de la même classe, par exemple :
            # def calculer(self):
            #     self.calculer()
            appel_methode_recursive = (
                isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == nom_fonction
                and isinstance(noeud.func.value, ast.Name)
                and noeud.func.value.id in {"self", "cls"}
            )

            # Si l'un des deux cas est vérifié, on enregistre
            # le nom de la fonction récursive.
            if appel_recursif or appel_methode_recursive:
                self.fonctions_recursives.add(nom_fonction)

        # On continue à parcourir les éventuels arguments de l'appel.
        self.generic_visit(noeud)


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
        # Paramètres nécessaires à l'estimation des émissions.
        self.puissance_machine:  float = 15.0 # puissance de ma machine en watts intel corei5
        self.pue: float = 1.0 #Power Usage Effectiveness.C'est un indicateur d'efficacité énergétique d'un centre de donnée (recommandé par le prof)
        self.intensite_carbone: float = 29.0 # d'apres le bilan électrique 2025 de RTE 
        self.vitesse_machine: float | None = None

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
        puissance = os.getenv("PUISSANCE_MACHINE_W")
        if puissance:
            try:
                self.puissance_machine = float(puissance)
            except ValueError :
                raise ValueError(
                    "PUISSANCE_MACHINE_W doit être un nombre."
                    )
        intensite = os.getenv("INTENSITE_CARBONE_G_KWH")    
        if intensite:
            try:
                self.intensite_carbone = float(intensite)
            except ValueError:
                raise ValueError(
                    "INTENSITE_CARBONE_G_KWH doit être un nombre."
                )

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

    def calculer_nombre_operations( self, fichier: Fichier,taille_reference: int) -> int:
        """
        Estime le nombre d'opérations à partir de l'exposant k
        et d'une taille de référence n.

        Modèle utilisé : nombre d'opérations = n^k.
        """

        if taille_reference < 1:
            raise ValueError(
                "La taille de référence doit être positive."
            )

        if fichier.complexite is None:
            raise ValueError(
                "La complexité du fichier n'est pas disponible."
            )

        if fichier.complexite < 0:
            raise ValueError(
                "La profondeur de complexité ne peut pas être négative."
            )

        nb_operations = taille_reference ** fichier.complexite

        return nb_operations
    
    def mesurer_vitesse_machine(self) -> float:
        """
        ici il mesure une vitesse indicative de calcul en opérations par seconde

        Le benchmark va utilise sum(range(1000)), pour  999 additions.
        """

        nombre_repetitions = 100_000

        temps = timeit.timeit(
            stmt="sum(range(1000))",
            number=nombre_repetitions
        )

        nombre_operations = 999 * nombre_repetitions

        if temps <= 0:
            raise RuntimeError(
                "Le temps de mesure est invalide."
            )

        self.vitesse_machine = nombre_operations / temps

        return self.vitesse_machine 

    def calculer_emissionCO2e(self, fichier: Fichier,nb_operations: int) -> float:
        """
        on estime les émissions de CO2e en grammes.

        Formules utilisées :
        1 kWh = 3 600 000 joules
        Temps = nombre_operations / vitesse_machine

        Energie (kWh) =
        Temps * puissance_machine * PUE / 3 600 000

        CO2e (g) = Energie * intensite_carbone
        """

        if nb_operations < 0:
            raise ValueError(
                "Le nombre d'opérations ne peut pas être négatif."
            )

        if (
            self.puissance_machine is None
            or self.puissance_machine <= 0
        ):
            raise ValueError(
                "La puissance de la machine doit être renseignée en watts."
            )

        if self.pue < 1:
            raise ValueError(
                "Le PUE doit être supérieur ou égal à 1."
            )

        if self.intensite_carbone < 0:
            raise ValueError(
                "L'intensité carbone ne peut pas être négative."
            )

        if self.vitesse_machine is None:
            self.mesurer_vitesse_machine()

        if self.vitesse_machine <= 0:
            raise ValueError(
                "La vitesse de la machine doit être positive."
            )

        # Estimation du temps d'exécution en secondes.
        temps_execution = nb_operations / self.vitesse_machine

        # Estimation de l'énergie consommée en kWh.
        energie_kWh = (
            temps_execution  * self.puissance_machine * self.pue  / 3_600_000)

        # Estimation des émissions en grammes de CO2e.
        emission = energie_kWh * self.intensite_carbone

        # Enregistrement dans le fichier analysé.
        fichier.emissionCO2 = emission

        return emission

    def estimer_emission_fichier( self,fichier: Fichier, taille_reference: int) -> float:
    """
    c'est pour réaliser l'estimation complète des émissions de CO2e d'un fichier.
    """

    #  1 analyser la profondeur maximale des boucles.
    complexite = self.analyser_complexite_code(fichier)

    if complexite is None:
        raise ValueError(
            "Impossible d'analyser la complexité du fichier."
        )

    # 2 : estimer le nombre d'opérations.
    nb_operations = self.calculer_nombre_operations(
        fichier,
        taille_reference
    )

    #  3 : calculer les émissions de CO2e.
    emission = self.calculer_emissionCO2e(
        fichier,
        nb_operations
    )

    return emission
    
def detecter_anti_patterns(self, fichier: Fichier) -> list[str] | None:
    """
    Recherche les anti-patterns dans un fichier Python.

    Retourne une liste des problèmes détectés.
    Retourne une liste vide si aucun problème n'est trouvé.
    Retourne None si le fichier ne peut pas être analysé.
    """

    try:
        # On récupère l'arbre syntaxique du fichier.
        # C'est cet arbre qui permet d'étudier la structure du code
        # sans avoir besoin de l'exécuter.
        arbre = fichier.obtenir_ast()

    except (ValueError, SyntaxError, UnicodeDecodeError):
        # Si le fichier n'est pas Python, contient une erreur de syntaxe
        # ou ne peut pas être lu, on ne peut pas faire l'analyse.
        return None

    # On crée un analyseur neuf pour ce fichier.
    analyseur = AnalyseurAntiPatterns()

    # On lance le parcours de l'arbre syntaxique.
    analyseur.visit(arbre)

    # On prépare la liste qui contiendra les problèmes trouvés.
    anti_patterns = []

    # Si au moins deux boucles sont imbriquées, on ajoute ce problème.
    if analyseur.boucles_imbriquees:
        anti_patterns.append("Boucles imbriquées")

    # On ajoute les fonctions dans lesquelles une récursivité directe
    # a été détectée.
    for nom in sorted(analyseur.fonctions_recursives):
        anti_patterns.append(
            f"Récursivité directe dans la fonction {nom}" )

    # On retourne tous les problèmes détectés.
    return anti_patterns 

