from business_object.audit import Audit
from business_object.dossier import Dossier
from dao.db_connection import DBConnection
from dao.fichier_dao import FichierDao
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class AuditDao(metaclass=Singleton):
    """Classe contenant différentes méthodes d'accès aux données des Audits dans la base de donnée."""

    @log
    def create_audit(self, audit: Audit, utilisateur_id: int) -> bool:
        """Créer un Audit et le stocke localement
        Arguments :
            audit (Audit) : Audit à créer
            utilisateur_id (int) : ID de l'utilisateur créant l'audit
        Returns:
            True si la création réussie, False sinon
        """
        res = None
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO audit(utilisateur_id, date_audit, statut, score, emissionCO2) VALUES "
                        "(%(utilisateur_id)s, %(date_audit)s, %(statut)s, %(score)s, %(emissionCO2)s) "
                        "RETURNING id;",
                        {
                            "utilisateur_id": utilisateur_id,
                            "date_audit": audit.date,
                            "statut": audit.statut,
                            "score": audit.score,
                            "emissionCO2": audit.emissionCO2_total,
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
    def update_audit(self, audit: Audit) -> bool:
        """Met à jour un Audit existant
        Arguments :
            audit (Audit) : Audit à mettre à jour
        Returns:
            True si la mise à jour réussie, False sinon
        """
        nb_affected_rows = 0
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE audit SET "
                        "date_audit = %(date_audit)s, "
                        "statut = %(statut)s, "
                        "score = %(score)s, "
                        "emissionCO2 = %(emissionCO2)s "
                        "WHERE id = %(id)s;",
                        {
                            "id": audit.id,
                            "date_audit": audit.date,
                            "statut": audit.statut,
                            "score": audit.score,
                            "emissionCO2": audit.emissionCO2_total,
                        },
                    )
                    nb_affected_rows = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return nb_affected_rows == 1

    @log
    def remove_audit(self, audit: Audit) -> bool:
        """Supprime un Audit existant
        Arguments :
            audit (Audit) : Audit à supprimer
        Returns:
            True si la suppression réussie, False sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM audit WHERE id = %(id)s;",
                        {
                            "id": audit.id,
                        },
                    )
                    res = cursor.rowcount
        except Exception as e:
            logger.error(e)
            raise

        return res > 0

    @log
    def find_audit(self, id_audit: int) -> Audit | None:
        """Recherche un Audit par son ID
        Arguments :
            id (int) : ID de l'Audit à rechercher
        Returns:
            Audit | None: audit correspondant, None sinon
        """
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, date_audit, statut, score, emissionCO2 "
                        "FROM audit WHERE id = %(id)s;",
                        {
                            "id": id_audit,
                        },
                    )
                    res = cursor.fetchone()
        except Exception as e:
            logger.error(e)
            raise

        audit = None
        if res:
            dossier = Dossier(
                nom="",
                chemin="",
                signature_HMAC="",
                liste_fichiers=FichierDao().find_by_audit(id_audit),
                date_soumission=res["date_audit"],
            )
            audit = Audit(
                id=res["id"],
                date=res["date_audit"],
                statut=res["statut"],
                score=res["score"],
                emissionCO2_total=res["emissionCO2"],
                dossier=dossier,
            )

        return audit
