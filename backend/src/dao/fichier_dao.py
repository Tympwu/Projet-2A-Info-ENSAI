import os
from pathlib import Path

from business_object.dossier import Dossier
from business_object.fichier import Fichier
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class FichierDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des fichiers dans la base de donnée."""

    @log
    def create_fichier(self, fichier: Fichier) -> bool:
        """Créer un fichier et le stocke localement
        Arguments :
            fichier (Fichier) : Fichier à créer
        Returns:
            True si la création réussie, False sinon
        """
        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Fichier(audit_id, chemin, extension, complexite, score, emissionCO2) VALUES "
                        "(%(chemin)s, %(extension)s, %(complexite)s, %(score)s, %(emissionCO2)s) "
                        "RETURNING id;",
                        {
                            "chemin": fichier.chemin,
                            "extension": fichier.extension,
                            "complexite": fichier.complexite,
                            "score": fichier.score,
                            "emissionco2": fichier.emissionCO2,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        created = False
        if res:
            fichier.id = res["id"]
            created = True

        return created

    @log
    def update_fichier(self, fichier: Fichier, id_audit: int | None = None) -> bool:
        """Met à jour un fichier dans la base de donnée
        Arguments:
            fichier (Fichier) : Fichier à mettre à jour
            id_audit (int): ID de l'audit correspondant au fichier, reste None si la valeur n'est pas déterminé
        Returns :
            True si la mise à jour est réussie, False sinon
        """
        nb_affected_rows = 0

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE fichier                        "
                        "   SET chemin = %(chemin)s,           "
                        "       audit_id = %(audit_id)s,       "
                        "       extension = %(extension)s,     "
                        "       score = %(score)s,             "
                        "       complexite = %(complexite)s,   "
                        "       emissionCO2 = %(emissionCO2)s, "
                        " WHERE id = %(id_fichier)s;           ",
                        {
                            "chemin": fichier.chemin,
                            "audit_id": id_audit,
                            "extension": fichier.extension,
                            "score": fichier.score,
                            "complexite": fichier.complexite,
                            "emissionco2": fichier.emissionCO2,
                            "id_fichier": fichier.id,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def remove_fichier(self, id_fichier: int) -> bool:
        """Supprime un fichier cible de la base de donnée
        Arguments:
            id_fichier (int) : Indice du fichier à supprimer
        Returns :
            True si la suppression est réussie, False sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM fichier WHERE id = %(id)s ",
                        {"id": id_fichier},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return res > 0

    @log
    def find_fichier(self, id_fichier: int) -> Fichier | None:
        """Trouve un fichier cible de la base de donnée
        Arguments:
            id_fichier (int) : Indice du fichier à trouver
        Returns :
            Fichier | None: fichier correspondant, None sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM Fichier WHERE id = %(id)s    ",
                        {"id": id_fichier},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        fichier = None
        if res:
            fichier = Fichier(
                id=res["id"],
                chemin=res["chemin"],
                complexite=res["complexite"],
                score=res["score"],
                emissionCO2=res["emissionco2"],
            )
        return fichier

    @log
    def find_by_utilisateur(self, id_utilisateur: int) -> list[Fichier]:
        """Trouve les fichiers dans la base de donnée liés à un utilisateur
        Arguments:
            id_utilisateur (int) : Indice de l'utilisateur pour lequel nous cherchons les fichiers
        Returns :
            list[Fichier]: Liste des fichiers correspondant, la liste peut être vide si aucun fichier n'est trouvé
        Raise:
            ValueError : L'id renseignée ne correspond pas à un utilisateur
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT f.* FROM utilisateurs u "
                        "JOIN audit a ON a.utilisateurs_id=u.id "
                        "JOIN fichier f ON f.audit_id=a.id "
                        "WHERE u.id=%(id_user)s",
                        {"id_user": id_utilisateur},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        fichiers = []
        if res:
            for row in res:
                fichiers.append(
                    Fichier(
                        id=row["id"],
                        extension=row["extension"],
                        chemin=row["chemin"],
                        complexite=row["complexite"],
                        score=row["score"],
                        emissionCO2=row["emissionco2"],
                    )
                )

        return fichiers

    @log
    def find_by_audit(self, id_audit: int) -> list[Fichier]:
        """Trouve les fichiers dans la base de donnée liés à un audit
        Arguments:
            id_audit (int) : Indice de l'audit pour lequel nous cherchons les fichiers
        Returns :
            list[Fichier]: Liste des fichiers correspondant, la liste peut être vide si aucun fichier n'est trouvé
        Raise:
            ValueError : L'id renseignée ne correspond pas à un audit
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT f.* FROM audit a "
                        "JOIN fichier f ON f.audit_id=a.id "
                        "WHERE a.id=%(id_audit)s",
                        {"id_audit": id_audit},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        fichiers = []
        if res:
            for row in res:
                fichiers.append(
                    Fichier(
                        id=row["id"],
                        extension=row["extension"],
                        chemin=row["chemin"],
                        complexite=row["complexite"],
                        score=row["score"],
                        emissionCO2=row["emissionco2"],
                    )
                )

        return fichiers

    @log
    def find_all(self) -> list[Fichier]:
        """Trouve les fichiers dans la base de donnée
        Returns :
            list[Fichier]: Liste des fichiers, la liste peut être vide si aucun fichier n'est trouvé
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM fichier ;",
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        fichiers = []
        if res:
            for row in res:
                fichiers.append(
                    Fichier(
                        id=row["id"],
                        extension=row["extension"],
                        chemin=row["chemin"],
                        complexite=row["complexite"],
                        score=row["score"],
                        emissionCO2=row["emissionco2"],
                    )
                )

        return fichiers

    @log
    def read_dossier(self, path: str) -> Dossier | None:
        """Créer un objet dossier avec tous les fichiers selon un chemin d'accès
        Arguments:
            path (str): chemin d'accès du dossier que tous les fichiers vont partager
        Returns:
            Dossier | None : Objet dossier contenant tous les fichiers à l'adresse donnée, None si aucun fichier n'a été trouvé
        """
        dossier_nom = Path(path).name
        path_normalise = path.rstrip(os.sep)
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM Fichier WHERE chemin LIKE %(path)s",
                        {"path": f"{path_normalise}/%"},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        fichiers = []
        dossier = None
        if res:
            for row in res:
                fichiers.append(
                    Fichier(
                        id=row["id"],
                        extension=row["extension"],
                        chemin=row["chemin"],
                        complexite=row["complexite"],
                        score=row["score"],
                        emissionCO2=row["emissionco2"],
                    )
                )
            dossier = Dossier(
                nom=dossier_nom,
                chemin=path_normalise,
                signature_HMAC="",
                liste_fichiers=fichiers,
                date_soumission=None,
            )
            logger.warning("Le chemin indiqué ne contient aucun fichier")
        return dossier

    @log
    def remove_dossier(self, path: str) -> bool:
        """Supprime tous les fichiers concernés par un dossier
        Arguments:
            path (str): chemin d'accès du dossier que tous les fichiers vont partager
        Returns:
            bool : True si la suppression est réussie, False sinon
        """
        path_normalise = path.rstrip(os.sep)
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM Fichier WHERE chemin LIKE %(path)s",
                        {"path": f"{path_normalise}/%"},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return res > 0

    @log
    def update_dossier(self, dossier_init: Dossier, dossier_nouv: Dossier) -> bool:
        """Met à jour une liste de fichiers contenu dans un dossier
        Arguments:
            dossier_init (Dossier): Dossier initial à mettre à jour
            dossier_nouv (Dossier): Nouveau dossier devant remplacer le précédent
        Returns:
            bool : True si la mise à jour est réussie, False sinon
        """
        path_normalise = dossier_init.chemin.rstrip(os.sep)
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM project.fichier WHERE (chemin LIKE %(path)s) "
                        "AND (audit_id IS NOT NULL);",
                        {"path": f"{path_normalise}/%"},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise
        if res:
            logger.error("Tentative de modification de dossier déjà traité")
            return False
        else:
            self.remove_dossier(dossier_init.chemin)
            for fichier in dossier_nouv.liste_fichiers:
                self.create_fichier(fichier)
        return True
