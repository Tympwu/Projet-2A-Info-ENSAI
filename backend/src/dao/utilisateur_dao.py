from business_object.utilisateur import Utilisateur
from dao.db_connection import DBConnection
from dao.historique_dao import HistoriqueDao
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
            utilisateur = Utilisateur(
                id=id_utilisateur,
                name=res["name"],
                email=res["email"],
                mot_de_passe=res["mot_de_passe"],
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
                historique = HistoriqueDao.find_by_utilisateur(row["id"])
                utilisateurs.append(Utilisateur(
                    id=row["id"],
                    name=nom_utilisateur,
                    email=res["email"],
                    mot_de_passe=res["mot_de_passe"],
                    historique=historique
                ))

        return utilisateurs

    @log
    def update(self, player) -> bool:
        """Update a player in the database.
        Args:
            Utilisateur to be updated
        Returns:
            True if update is successful, False otherwise
        """
        nb_affected_rows = 0

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE player                                                  "
                        "   SET username = %(username)s,                                "
                        "       password = COALESCE(%(password)s, password),            "
                        "       elo = %(elo)s,                                          "
                        "       email = %(email)s,                                      "
                        "       pokemon_fan = %(pokemon_fan)s,                          "
                        "       access_token = COALESCE(%(access_token)s, access_token) "
                        " WHERE id_player = %(id_player)s;                              ",
                        {
                            "username": player.username,
                            "password": player.password,
                            "elo": player.elo,
                            "email": player.email,
                            "pokemon_fan": player.pokemon_fan,
                            "access_token": player.access_token,
                            "id_player": player.id_player,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def delete(self, player) -> bool:
        """Delete a player from the database.
        Args:
            Utilisateur to delete from the database
        Returns:
            True if the player was successfully deleted, False otherwise
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM player                               "
                        " WHERE id_player = %(id_player)s                 ",
                        {"id_player": player.id_player},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return res > 0

    @log
    def login(self, username: str, password: str) -> Utilisateur:
        """Login using username and password.
        Args:
            username (str)
            password (str)
        Returns:
            Utilisateur or None
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                               "
                        "  FROM player                          "
                        " WHERE username = %(username)s         "
                        "   AND password = %(password)s;        ",
                        {"username": username, "password": password},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        player = None

        if res:
            player = Utilisateur(
                username=res["username"],
                password=res["password"],
                elo=res["elo"],
                email=res["email"],
                pokemon_fan=res["pokemon_fan"],
                access_token=res["access_token"],
                id_player=res["id_player"],
            )

        return player

    @log
    def find_by_token(self, access_token: str) -> Utilisateur:
        """Find a player by their access token.
        Args:
            access_token (str): The token to search for.
        Returns:
            Utilisateur object if found, otherwise None.
        """
        if not access_token:
            return None

        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                "
                        "  FROM player                           "
                        " WHERE access_token = %(token)s;        ",
                        {"token": access_token},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error finding player by token: {e}")
            raise

        player = None
        if res:
            player = Utilisateur(
                id_player=res["id_player"],
                username=res["username"],
                password=res["password"],
                elo=res["elo"],
                email=res["email"],
                pokemon_fan=res["pokemon_fan"],
                access_token=res["access_token"],
            )

        return player
