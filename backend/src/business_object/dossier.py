from datetime import datetime

from .fichier import Fichier


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

    # def obtenir_dependances_dossiers() pas compris si on voulait rassembler toutes les
    # dépendances présentes dans le dossier ?
    # -> Pour moi oui, faut checker toutes les dépendances des fichiers dans le dosier et renvoyer l'ensemble avec un
    # format sympa (genre {"dependance1" : version, ...})

    def __repr__(self) -> str:
        """
        Représentation textuelle du dossier

        Returns
        -------
        str: Nom du dossier et nombre de fichiers.
        """
        return f"Dossier({self.nom!r}, {len(self.liste_fichiers)} fichier"
