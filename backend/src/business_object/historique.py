from business_object.audit import Audit


class Historique:
    """
    Regroupe les audits réalisés par un utilisateur.

    Attributes
    ---------
    id (int): Identifiant unique de l'historique (correspond à Utilisateur.id_historique).
    audits (list[Audit]): Audits de l'historique, dans l'ordre d'ajout.
    """

    def __init__(self, id: int, audits: list[Audit] | None) -> None:
        """
        Initialise un historique.

        Parameters
        ----------
        id (int): Identifiant unique de l'historique.
        audits (list[Audit] | None): Audits initiaux (optionnel, vide par défaut).
        """
        self.id = id
        self.audits = audits or []

    def consulter_historique(self) -> list[Audit]:
        """
        Retourne tous les audits contenus dans l'historique.

        Returns
        -------
        list[Audit]: Liste des audits.
        """
        return self.audits

    def ajout_historique(self, audit: Audit) -> None:
        """
        Ajoute un audit à la fin de l'historique.

        Paramètres
        ----------
        audit (Audit): Audit à ajouter.

        Returns
        -------
        None
        """
        self.audits.append(audit)

    def consulter_audit(self, id_audit: int) -> Audit:
        """
        Recherche un audit par son identifiant dans l'historique

        Parameters
        ----------
        id_audit (int): Identifiant de l'audit recherché.

        Returns
        -------
        Audit | None: L'audit trouvé, ou None.
        """
        for audit in self.audits:
            if audit.id == id_audit:
                return audit
        return None
