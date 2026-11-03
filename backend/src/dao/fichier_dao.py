from business_object.fichier import Fichier
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class FichierDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des fichiers dans la base de donnée."""

    @log
    def create_fichier(self, fichier: Fichier, audit_id: int) -> bool:
        """Créer un fichier et le stocke localement
        Arguments :
            fichier (Fichier) : Fichier à créer
            audit_id (int) : ID de l'audit contenant le fichier
        Returns:
            True si la création réussie, False sinon
        """
        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Fichier(audit_id, chemin, extension, complexite, score, emissionCO2) VALUES "
                        "(%(audit_id)s,%(chemin)s, %(extension)s, %(complexite)s, %(score)s, %(emissionCO2)s) "
                        "RETURNING id;",
                        {
                            "audit_id": audit_id,
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
    def update_fichier(self, fichier: Fichier) -> bool:
        """Met à jour un fichier dans la base de donnée
        Arguments:
            fichier (Fichier) : Fichier à mettre à jour
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
                        "       extension = %(extension)s,     "
                        "       score = %(score)s,             "
                        "       complexite = %(complexite)s,   "
                        "       emissionCO2 = %(emissionCO2)s, "
                        " WHERE id = %(id_fichier)s;           ",
                        {
                            "chemin": fichier.chemin,
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
                extension=res["extension"],
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
