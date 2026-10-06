from business_object.utilisateur import Utilisateur
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class UtilisateurDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des utilisateurs dans la base de donnée."""

    @log
    def create(self, user) -> bool:
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
                            "mot_de_passe": user.mot_de_passe,
                            "name": user.name,
                            "email": user.email,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        created = False
        if res:
            user.id = res["id"]
            created = True

        return created

    @log
    def find_by_id(self, id_user: int) -> Utilisateur:
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
                        {"id_user": id_user},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        utilisateur = None
        if res:
            utilisateur = Utilisateur(
                id=id_user,
                email=res["email"],
                mot_de_passe=res["mot_de_passe"],
            )

        return utilisateur

    @log
    def find_all(self) -> list[Player]:
        """List all players in the database.
        Returns:
            list[Player] sorted by username
        """

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT *                                "
                        "  FROM player                           "
                        " ORDER BY username;                     "
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        players_list = []

        if res:
            for row in res:
                player = Player(
                    id_player=row["id_player"],
                    username=row["username"],
                    password=row["password"],
                    elo=row["elo"],
                    email=row["email"],
                    pokemon_fan=row["pokemon_fan"],
                )

                players_list.append(player)

        return players_list

    @log
    def update(self, player) -> bool:
        """Update a player in the database.
        Args:
            Player to be updated
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
            Player to delete from the database
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
    def login(self, username: str, password: str) -> Player:
        """Login using username and password.
        Args:
            username (str)
            password (str)
        Returns:
            Player or None
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
            player = Player(
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
    def find_by_token(self, access_token: str) -> Player:
        """Find a player by their access token.
        Args:
            access_token (str): The token to search for.
        Returns:
            Player object if found, otherwise None.
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
            player = Player(
                id_player=res["id_player"],
                username=res["username"],
                password=res["password"],
                elo=res["elo"],
                email=res["email"],
                pokemon_fan=res["pokemon_fan"],
                access_token=res["access_token"],
            )

        return player
