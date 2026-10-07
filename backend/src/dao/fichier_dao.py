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
                        "INSERT INTO Fichier(chemin, extension, complexite, score, emissionCO2) VALUES "
                        "(%(chemin)s, %(extension)s, %(complexite)s, %(score)s, %(emissionCO2)s) "
                        "RETURNING id;",
                        {
                            "chemin": fichier.chemin,
                            "extension": fichier.extension,
                            "complexite": fichier.complexite,
                            "score": fichier.score,
                            "emissionCO2": fichier.emissionCO2,
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
                            "emissionCO2": fichier.emissionCO2,
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
        pass

    @log
    def find_fichier(self, id_fichier: int) -> Fichier | None:
        """Trouve un fichier cible de la base de donnée
        Arguments:
            id_fichier (int) : Indice du fichier à trouver
        Returns :
            Fichier | None: fichier correspondant, None sinon
        """
        pass

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
        pass
