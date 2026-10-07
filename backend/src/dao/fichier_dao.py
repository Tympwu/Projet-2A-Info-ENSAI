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

    def remove_fichier(self, id_fichier: int) -> bool:
        pass

    def find_fichier(self, id_fichier: int) -> bool:
        pass

    def find_by_utilisateur(self, id_utilisateur: int) -> list[Fichier]:
        pass
