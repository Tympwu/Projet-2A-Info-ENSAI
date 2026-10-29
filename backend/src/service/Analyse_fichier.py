import os

from dotenv import load_dotenv


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

        # Pour l'instant, on met pas  consommation_estimee_kWh et
        # emissionCO2e. Ce sont des résultats propres à chaque fichier
        # (Fichier.emissionCO2 existe déjà), donc ils ne doivent pas être
        # stockés ici. Les coefficients de configuration nécessaires au calcul
        # du CO2 seront ajoutés ici plus tard, quand on saura quel calcul faire.