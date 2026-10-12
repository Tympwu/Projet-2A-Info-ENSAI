from business_object.audit import Audit
from dao.fichier_dao import FichierDao
from dao.db_connection import DBConnection
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class AuditDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des Audits dans la base de donnée."""

    @log
    def create_audit(self, audit: Audit) -> bool:
        """Créer un Audit et le stocke localement
        Arguments :
            audit (Audit) : Audit à créer
        Returns:
            True si la création réussie, False sinon
        """
        res = None
        ##### A ADAPTER
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute( 
                        "INSERT INTO audit(historique_id, date_audit, complexite, score, emissionCO2) VALUES "
                        "(%(chemin)s, %(extension)s, %(complexite)s, %(score)s, %(emissionCO2)s) "
                        "RETURNING id;",
                        {
                            "chemin": Audit.chemin,
                            "extension": Audit.extension,
                            "complexite": Audit.complexite,
                            "score": Audit.score,
                            "emissionCO2": Audit.emissionCO2,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        created = False
        if res:
            Audit.id = res["id"]
            created = True

        return created

    @log
    def update_Audit(self, Audit: Audit) -> bool:
        """Met à jour un Audit dans la base de donnée
        Arguments:
            Audit (Audit) : Audit à mettre à jour
        Returns :
            True si la mise à jour est réussie, False sinon
        """
        nb_affected_rows = 0

        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE Audit                        "
                        "   SET chemin = %(chemin)s,           "
                        "       extension = %(extension)s,     "
                        "       score = %(score)s,             "
                        "       complexite = %(complexite)s,   "
                        "       emissionCO2 = %(emissionCO2)s, "
                        " WHERE id = %(id_Audit)s;           ",
                        {
                            "chemin": Audit.chemin,
                            "extension": Audit.extension,
                            "score": Audit.score,
                            "complexite": Audit.complexite,
                            "emissionCO2": Audit.emissionCO2,
                            "id_Audit": Audit.id,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def remove_Audit(self, id_Audit: int) -> bool:
        """Supprime un Audit cible de la base de donnée
        Arguments:
            id_Audit (int) : Indice du Audit à supprimer
        Returns :
            True si la suppression est réussie, False sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM Audit WHERE id = %(id)s ",
                        {"id": id_Audit},
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return res > 0

    @log
    def find_Audit(self, id_Audit: int) -> Audit | None:
        """Trouve un Audit cible de la base de donnée
        Arguments:
            id_Audit (int) : Indice du Audit à trouver
        Returns :
            Audit | None: Audit correspondant, None sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor as cursor:
                    cursor.execute(
                        "SELECT * FROM AuditWHERE id = %(id)s    ",
                        {"id": id_Audit},
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        Audit = None
        if res:
            Audit = Audit(
                id=res["id"],
                nom=res["extension"],
                chemin=res["chemin"],
                complexite=res["complexite"],
                score=res["score"],
                emissionCO2=res["emissionCO2"],
            )
        return Audit

    @log
    def find_by_utilisateur(self, id_utilisateur: int) -> list[Audit]:
        """Trouve les Audits dans la base de donnée liés à un utilisateur
        Arguments:
            id_utilisateur (int) : Indice de l'utilisateur pour lequel nous cherchons les Audits
        Returns :
            list[Audit]: Liste des Audits correspondant, la liste peut être vide si aucun Audit n'est trouvé
        Raise:
            ValueError : L'id renseignée ne correspond pas à un utilisateur
        """
        try:
            with DBConnection.connection as connection:
                with connection.cursor as cursor:
                    cursor.excecute(
                        "SELECT f.* FROM project.utilisateurs u"
                        "JOIN project.historique h ON h.utilisateur_id=u.id"
                        "JOIN project.audit a ON a.historique_id=h.id"
                        "JOIN project.Audit f ON f.audit_id=a.id"
                        "WHERE u.id=%(id_user)s",
                        {"id_user": id_utilisateur},
                    )
                    res = cursor.fetchall()
        except Exception as e:
            logger.error(e)
            raise

        Audits = []
        if res:
            for row in res:
                Audits.append(
                    Audit(
                        id=row["id"],
                        nom=row["extension"],
                        chemin=row["chemin"],
                        complexite=row["complexite"],
                        score=row["score"],
                        emissionCO2=row["emissionCO2"],
                    )
                )

        return Audits
