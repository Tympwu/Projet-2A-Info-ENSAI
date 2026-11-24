import ast
import json
import logging
import os
import timeit
import urllib.error
import urllib.request

from cvss import CVSS3, CVSS4
from cvss.exceptions import CVSSError
from dotenv import load_dotenv

from business_object.dependance import Dependances
from business_object.fichier import Fichier
from business_object.vulnerabilite import Vulnerabilite
from utils.singleton import Singleton

logger = logging.getLogger(__name__)


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
        # generic_visit() pour déléguer à NodeVisitor le parcours récursif de l'ensemble des sous-nœuds d'une boucle
        # visite automatiquement tous les sous-nœuds du nœud courant.
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
        """Visite une boucle for/while et note si elle est imbriquée dans une autre."""
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
        """Visite une fonction en retenant son nom, pour repérer ses appels récursifs."""
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
        """Repère un appel de la fonction en cours d'analyse, c'est-à-dire une récursion."""
        # On vérifie les appels uniquement si on se trouve dans une fonction.
        if self.fonctions:
            # Nom de la fonction actuellement analysée.
            nom_fonction = self.fonctions[-1]

            # Cas 1 : appel direct, par exemple :
            # def calculer():
            #     calculer()
            appel_recursif = isinstance(noeud.func, ast.Name) and noeud.func.id == nom_fonction

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


class Analyse_fichier(metaclass=Singleton):
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
    ECOSYSTEME (str): Écosystème interrogé dans l'API OSV (ici "PyPI").
    TIMEOUT_OSV (int): Délai maximal d'attente de l'API, en secondes.
    SEUIL_VULNERABILITE (float): Score (0 à 10) à partir duquel une vulnérabilité est retenue.
    DESCRIPTION_INDISPONIBLE (str): Description utilisée quand l'API ne donne pas de résumé.
    SCORES_PAR_ETIQUETTE (dict[str, float]): Score attribué à une étiquette de gravité
    (LOW, HIGH...) quand la fiche n'a pas de vecteur CVSS.
    """

    URL_OSV_PAR_DEFAUT = "https://api.osv.dev/v1/query"
    ECOSYSTEME = "PyPI"
    TIMEOUT_OSV = 10
    # 7.0 est le début de la catégorie « High » de l'échelle CVSS v3 et v4.
    SEUIL_VULNERABILITE = 7.0
    DESCRIPTION_INDISPONIBLE = "description indisponible"

    # Valeurs choisies par convention (une valeur représentative par niveau), pas des scores
    # CVSS : elles ne servent que lorsque la fiche n'a qu'une étiquette de gravité :
    SCORES_PAR_ETIQUETTE = {
        "LOW": 3.0,
        "MODERATE": 5.0,
        "MEDIUM": 5.0,
        "HIGH": 8.0,
        "CRITICAL": 10.0,
    }

    def __init__(self) -> None:
        """
        Initialise l'analyseur et charge sa configuration.

        Returns
        -------
        None
        """
        self.api_url_OSV: str = self.URL_OSV_PAR_DEFAUT
        # Paramètres nécessaires à l'estimation des émissions.
        self.puissance_machine: float = 15.0  # puissance de ma machine en watts intel corei5
        self.pue: float = 1.0  # Power Usage Effectiveness.C'est un indicateur d'efficacité énergétique d'un centre de donnée (recommandé par le prof)
        self.intensite_carbone: float = 29.0  # d'apres le bilan électrique 2025 de RTE
        self.vitesse_machine: float | None = None

        # Liste de dépendances analysés
        self.view_dependances = {}

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
        if not self.api_url_OSV.startswith("https://"):
            raise ValueError("OSV_API_URL doit être une adresse https://.")
        puissance = os.getenv(
            "PUISSANCE_MACHINE_W", 15.0
        )  # Valeur temporaire à changer le temps d'obtenir la vraie valeur dans le .env
        if puissance:
            try:
                self.puissance_machine = float(puissance)
            except ValueError:
                raise ValueError("PUISSANCE_MACHINE_W doit être un nombre.") from ValueError
        intensite = os.getenv("INTENSITE_CARBONE_G_KWH")
        if intensite:
            try:
                self.intensite_carbone = float(intensite)
            except ValueError:
                raise ValueError("INTENSITE_CARBONE_G_KWH doit être un nombre.") from ValueError

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

    def calculer_nombre_operations(self, fichier: Fichier, taille_reference: int) -> int:
        """
        Estime le nombre d'opérations à partir de l'exposant k
        et d'une taille de référence n.

        Modèle utilisé : nombre d'opérations = n^k.
        """

        if taille_reference < 1:
            raise ValueError("La taille de référence doit être positive.")

        if fichier.complexite is None:
            raise ValueError("La complexité du fichier n'est pas disponible.")

        if fichier.complexite < 0:
            raise ValueError("La profondeur de complexité ne peut pas être négative.")

        nb_operations = taille_reference**fichier.complexite

        return nb_operations

    def mesurer_vitesse_machine(self) -> float:
        """
        ici il mesure une vitesse indicative de calcul en opérations par seconde

        Le benchmark va utilise sum(range(1000)), pour  999 additions.
        """

        nombre_repetitions = 100_000

        temps = timeit.timeit(stmt="sum(range(1000))", number=nombre_repetitions)

        nombre_operations = 999 * nombre_repetitions

        if temps <= 0:
            raise RuntimeError("Le temps de mesure est invalide.")

        self.vitesse_machine = nombre_operations / temps

        return self.vitesse_machine

    def calculer_emissionCO2e(self, fichier: Fichier, nb_operations: int) -> float:
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
            raise ValueError("Le nombre d'opérations ne peut pas être négatif.")

        if self.puissance_machine is None or self.puissance_machine <= 0:
            raise ValueError("La puissance de la machine doit être renseignée en watts.")

        if self.pue < 1:
            raise ValueError("Le PUE doit être supérieur ou égal à 1.")

        if self.intensite_carbone < 0:
            raise ValueError("L'intensité carbone ne peut pas être négative.")

        if self.vitesse_machine is None:
            self.mesurer_vitesse_machine()

        if self.vitesse_machine <= 0:
            raise ValueError("La vitesse de la machine doit être positive.")

        # Estimation du temps d'exécution en secondes.
        temps_execution = nb_operations / self.vitesse_machine

        # Estimation de l'énergie consommée en kWh.
        energie_kWh = temps_execution * self.puissance_machine * self.pue / 3_600_000

        # Estimation des émissions en grammes de CO2e.
        emission = energie_kWh * self.intensite_carbone

        # Enregistrement dans le fichier analysé.
        fichier.emissionCO2 = emission

        return emission

    def estimer_emission_fichier(self, fichier: Fichier, taille_reference: int) -> float:
        """
        c'est pour réaliser l'estimation complète des émissions de CO2e d'un fichier.
        """

        #  1 analyser la profondeur maximale des boucles.
        complexite = self.analyser_complexite_code(fichier)

        if complexite is None:
            raise ValueError("Impossible d'analyser la complexité du fichier.")

        # 2 : estimer le nombre d'opérations.
        nb_operations = self.calculer_nombre_operations(fichier, taille_reference)

        #  3 : calculer les émissions de CO2e.
        emission = self.calculer_emissionCO2e(fichier, nb_operations)

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
            anti_patterns.append(f"Récursivité directe dans la fonction {nom}")

        # On retourne tous les problèmes détectés.
        return anti_patterns

    def analyse_dependances(self, fichier: Fichier) -> bool:
        """Cherche les vulnérabilités connues des dépendances du fichier et en déduit son score.

        Interroge l'API OSV pour chaque dépendance dont la version est connue (une dépendance
        sans version ne peut pas être interrogée : elle est ignorée). Le score d'une dépendance
        est celui de sa pire vulnérabilité ; celui du fichier est le plus grand score de ses
        dépendances (0 s'il n'y en a aucune). Chaque vulnérabilité dont le score atteint
        `SEUIL_VULNERABILITE` est rangée dans `fichier.liste_vulnerabilites`. Le score du
        fichier est écrit dans `fichier.score`.

        Les vulnérabilités sans aucune indication de gravité ne sont ni retenues ni comptées
        dans le score : elles sont signalées dans les journaux.

        Args:
            fichier (Fichier): Fichier à analyser.

        Returns:
            bool: True si l'analyse a réussi, False sinon : dépendances non extractibles, ou
            API injoignable (`fichier.score` et `fichier.liste_vulnerabilites` valent alors None).
        """

        if fichier.liste_dependances is None:
            fichier.extraire_dependances()
        if fichier.liste_dependances is None:
            fichier.liste_vulnerabilites = None
            fichier.score = None
            return False

        retenues: list[Vulnerabilite] = []
        score_fichier = 0.0

        try:
            for dependance in fichier.liste_dependances:
                # L'API a besoin d'une version précise pour répondre.
                # du coup on a une limite  : une dépendance sans version (simple import dans un .py, ou
                # version non épinglée) ne peut pas être interrogée et n'entre pas dans le
                # score.
                if dependance.version is None:
                    logger.warning("Dépendance %s : version inconnue.", dependance.nom)

                for fiche in self._interroger_osv(dependance):
                    score = self._score_vulnerabilite(fiche)
                    identifiant = fiche.get("id", "identifiant inconnu")
                    if score is None:
                        logger.warning("Vulnérabilité %s ignorée : gravité inconnue.", identifiant)
                        continue

                    # Maximum : une seule faille grave suffit à rendre le fichier grave.
                    score_fichier = max(score_fichier, score)
                    if score >= self.SEUIL_VULNERABILITE:
                        resume = fiche.get("summary") or self.DESCRIPTION_INDISPONIBLE
                        retenues.append(
                            Vulnerabilite(
                                description=f"{identifiant} : {resume}", score_danger=score
                            )
                        )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            # Une panne réseau ne doit jamais passer pour « aucune vulnérabilité » : on
            # n'enregistre aucun résultat partiel.
            fichier.liste_vulnerabilites = None
            fichier.score = None
            return False

        fichier.liste_vulnerabilites = retenues
        fichier.score = score_fichier
        return True

    def _interroger_osv(self, dependance: Dependances) -> list[dict]:
        """Récupère les fiches de vulnérabilités d'une dépendance auprès de l'API OSV.

        Suit les pages de résultats : quand la réponse contient un `next_page_token`, la requête
        est renvoyée avec ce jeton, jusqu'à la dernière page.

        Args:
            dependance (Dependances): Dépendance à interroger (nom et version renseignés).

        Returns:
            list[dict]: Les fiches telles que renvoyées par l'API (liste vide si aucune).

        Raises:
            urllib.error.URLError: Si l'API est injoignable ou répond par une erreur.
            TimeoutError: Si l'API ne répond pas à temps.
            json.JSONDecodeError: Si la réponse n'est pas du JSON valide.
        """
        # Les failles dépendent de la version : la clé du cache est (nom, version).
        cle = (dependance.nom, dependance.version)
        if cle in self.view_dependances:
            return self.view_dependances[cle]
        fiches: list[dict] = []
        jeton = None
        while True:
            corps = {"package": {"name": dependance.nom, "ecosystem": self.ECOSYSTEME}}
            if dependance.version:
                corps["version"] = dependance.version
            if jeton:
                corps["page_token"] = jeton
            requete = urllib.request.Request(
                self.api_url_OSV,
                data=json.dumps(corps).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # L'URL vient de la configuration (OSV_API_URL) et est vérifiée à l'initialisation :
            # seul le schéma https est accepté, d'où l'exception bandit B310.
            with urllib.request.urlopen(requete, timeout=self.TIMEOUT_OSV) as reponse:  # nosec B310
                donnees = json.load(reponse)
            fiches.extend(donnees.get("vulns", []))
            jeton = donnees.get("next_page_token")
            if not jeton:
                self.view_dependances[cle] = fiches
                return fiches

    def _score_vulnerabilite(self, fiche: dict) -> float | None:
        """Donne le score (0 à 10) d'une fiche de vulnérabilité.

        Ordre de préférence : le vecteur CVSS (le plus élevé s'il y en a plusieurs), puis
        l'étiquette de gravité (`database_specific.severity`).

        Args:
            fiche (dict): Fiche renvoyée par l'API OSV.

        Returns:
            float | None: Le score, ou None si la fiche n'indique aucune gravité exploitable.
        """
        scores = []
        for gravite in fiche.get("severity", []):
            score = self._convertir_score(str(gravite.get("score", "")))
            if score is not None:
                scores.append(score)
        if scores:
            return max(scores)

        specifique = fiche.get("database_specific")
        if isinstance(specifique, dict):
            return self.SCORES_PAR_ETIQUETTE.get(str(specifique.get("severity", "")).upper())
        return None

    @staticmethod
    def _convertir_score(texte: str) -> float | None:
        """Convertit le champ `score` d'une gravité OSV en nombre entre 0 et 10.

        Le champ contient en général un vecteur CVSS (`CVSS:3.1/AV:N/...`), parfois directement
        un nombre.

        Args:
            texte (str): Contenu du champ `score`.

        Returns:
            float | None: Le score, ou None si le texte n'est ni un nombre entre 0 et 10 ni un
            vecteur CVSS 3.x ou 4.0 valide.
        """
        try:
            nombre = float(texte)
        except ValueError:
            nombre = None
        if nombre is not None:
            return nombre if 0 <= nombre <= 10 else None

        try:
            if texte.startswith("CVSS:4"):
                return float(CVSS4(texte).base_score)
            if texte.startswith("CVSS:3"):
                return float(CVSS3(texte).scores()[0])
        except CVSSError:
            return None
        return None
