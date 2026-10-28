from datetime import datetime

from business_object.dépendance import Dependances
from business_object.fichier import Fichier


class Dossier:
    """
    Représente un dossier soumis pour être audité.

    Un dossier regroupe l'ensemble des fichiers à analyser et porte une
    signature HMAC permettant de vérifier son intégrité.

    Attributs
    ---------
    nom (str): Nom du dossier.
    date_soumission (datetime): Date et heure de soumission.
    chemin (str): Chemin du dossier sur le disque.
    liste_fichiers (list[Fichier]): Fichiers contenus dans le dossier.
    _signature_HMAC (str): Signature HMAC du dossier (attribut privé).

    """

    def __init__(
        self,
        nom: str,
        chemin: str,
        signature_HMAC: str,
        liste_fichiers: list[Fichier],
        date_soumission: datetime | None = None,
    ) -> None:
        """
        Initialise un dossier.

        Paramètres
        ----------
        nom (str): Nom du dossier.
        chemin (str): Chemin du dossier sur le disque.
        liste_fichiers (list[Fichier] | None): Fichiers du dossier
        signature_HMAC (str): Signature d'intégrité du dossier
        date_soumission (datetime | None): Date de soumission

        """
        self.nom: str = nom
        self.chemin: str = chemin
        self._signature_HMAC: str = signature_HMAC
        self.liste_fichiers: list[Fichier] = liste_fichiers
        self.date_soumission: datetime = date_soumission or datetime.now()

    def obtenir_fichiers(self) -> list[Fichier]:
        """
        Retourne les fichiers du dossier.

        Returns
        -------
        list[Fichier]: Liste des fichiers (vide si aucun).
        """
        return self.liste_fichiers

    def obtenir_dependances_dossier(self) -> list[Dependances]:
        """
        Rassemble les dépendances de tous les fichiers du dossier.

        Parcourt les dépendances de chaque fichier et les regroupe dans une
        seule liste. Une dépendance utilisée par plusieurs fichiers n'apparaît
        qu'une fois (deux dépendances sont identiques si leur nom et leur
        version sont identiques).

        Returns
        -------
        list[Dependances]: Dépendances du dossier, sans doublons
        (vide si aucun fichier n'a de dépendance).
        """
        vues = set()
        resultat: list[Dependances] = []
        for fichier in self.liste_fichiers:
            for dep in fichier.obtenir_dependances_fichier():
                cle = (dep.nom, dep.version)
                if cle not in vues:
                    vues.add(cle)
                    resultat.append(dep)
        return resultat

    def __repr__(self) -> str:
        """
        Représentation textuelle du dossier

        Returns
        -------
        str: Nom du dossier et nombre de fichiers.
        """
        return f"Dossier({self.nom!r}, {len(self.liste_fichiers)} fichier"
