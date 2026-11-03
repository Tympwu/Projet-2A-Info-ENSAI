from business_object.historique import Historique
from business_object.utilisateur import Utilisateur
from dao.audit_dao import AuditDao
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class UtilisateurDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des utilisateurs dans la base de donnée."""

    @log
    def create_utilisateur(self, utilisateur) -> bool:
        """Créer un utilisateur dans la base de donnée
        Arguments :
            user (Utilisateur) : Utilisateur à créer
        Returns:
            True si la création réussie, False sinon
        """
        res = None

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Utilisateurs(mot_de_passe, name, email) VALUES "
                        "(%(mot_de_passe)s, %(name)s, %(email)s) "
                        "RETURNING id;",
                        {
                            "mot_de_passe": utilisateur.mot_de_passe,
                            "name": utilisateur.name,
                            "email": utilisateur.email,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        created = False
        if res:
            utilisateur.id = res["id"]
            created = True

        return created

    @log
    def find_utilisateur(self, id_utilisateur: int) -> Utilisateur:
        """Trouve un utilisateur par son id.
        Arguments :
            id_user (int): L'ID de l'utilisateur à trouver
        Returns:
            Utilisateur avec l'ID correspondant
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                 "
                        "  FROM utilisateurs                      "
                        " WHERE id = %(id_user)s;   ",
                        {"id_user": id_utilisateur},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        utilisateur = None
        if res:
            historique = Historique(
                id=id_utilisateur,
                audits=AuditDao().find_by_utilisateur(id_utilisateur),
            )
            utilisateur = Utilisateur(
                id=id_utilisateur,
                name=res["name"],
                email=res["email"],
                mot_de_passe=res["mot_de_passe"],
                historique=historique,
            )

        return utilisateur

    @log
    def find_utilisateur_by_name(self, nom_utilisateur: int) -> list[Utilisateur]:
        """Trouve tous les utilisateur ayant le nom recherché.
        Arguments :
            nom_utilisateur (str): Le nom de(s) l'utilisateur à rechercher
        Returns:
            Liste d'utilisateur avec le nom correspondant
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                 "
                        "  FROM utilisateurs                      "
                        " WHERE name = %(name_user)s;   ",
                        {"name_user": nom_utilisateur},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        utilisateurs = []
        if res:
            for row in res:
                historique = Historique(
                    id=row["id"],
                    audits=AuditDao().find_by_utilisateur(row["id"]),
                )
                utilisateurs.append(
                    Utilisateur(
                        id=row["id"],
                        name=nom_utilisateur,
                        email=res["email"],
                        mot_de_passe=res["mot_de_passe"],
                        historique=historique,
                    )
                )

        return utilisateurs

    @log
    def find_all(self) -> list[Utilisateur]:
        """Trouve tous les utilisateur de la base de donnée.
        Returns:
            list[Utilisateur] : Liste d'utilisateurs de la base de donnée
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM utilisateurs;",
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        utilisateurs = []
        if res:
            for row in res:
                historique = Historique(
                    id=row["id"],
                    audits=AuditDao().find_by_utilisateur(row["id"]),
                )
                utilisateurs.append(
                    Utilisateur(
                        id=row["id"],
                        name=row["name"],
                        email=res["email"],
                        mot_de_passe=res["mot_de_passe"],
                        historique=historique,
                    )
                )

        return utilisateurs

    @log
    def update_utilisateur(self, utilisateur) -> bool:
        """Met à jour un utilisateur dans la base de données
        Arguments:
            utilisateur (Utilisateur) : Utilisateur à mettre à jour
        Returns :
            True si la mise à jour est réussie, False sinon
        """
        nb_affected_rows = 0

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE Utilisateurs                      "
                        "   SET mot_de_passe = %(mot_de_passe)s,  "
                        "       name = %(name)s,                  "
                        "       email = %(email)s                 "
                        " WHERE id = %(id_utilisateur)s;         ",
                        {
                            "mot_de_passe": utilisateur.mot_de_passe,
                            "name": utilisateur.name,
                            "email": utilisateur.email,
                            "id_utilisateur": utilisateur.id,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def remove_utilisateur(self, utilisateur) -> bool:
        """Supprime un utilisateur de la base de données
        Arguments:
            utilisateur (Utilisateur) : Utilisateur à supprimer
        Returns :
            True si la suppression est réussie, False sinon
        """
        nb_affected_rows = 0

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM Utilisateurs            WHERE id = %(id_utilisateur)s;   ",
                        {
                            "id_utilisateur": utilisateur.id,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def login_utilisateur(self, nom: str, mot_de_passe: str) -> Utilisateur | None:
        """Permet à l'utilisateur de se connecter.
        Args:
            nom (str) : nom de l'utilisateur
            mot_de_passe (str) : mot de passe de l'utilisateur
        Returns:
            Utilisateur ou None
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                               "
                        "  FROM Utilisateurs                    "
                        " WHERE name = %(name)s                 "
                        "   AND mot_de_passe = %(mot_de_passe)s;",
                        {"name": nom, "mot_de_passe": mot_de_passe},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        player = None

        if res:
            historique = Historique(id=res["id"], audits=AuditDao().find_by_utilisateur(res["id"]))
            player = Utilisateur(
                name=res["name"],
                mot_de_passe=res["mot_de_passe"],
                id=res["id"],
                email=res["email"],
                historique=historique,
            )

        return player
