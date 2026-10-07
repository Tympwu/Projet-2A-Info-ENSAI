from business_object.historique import Historique
from dao.db_connection import DBConnection
from dao.fichier_dao import FichierDao
from utils.log_utils import get_logger, log
from utils.singleton import Singleton

logger = get_logger(__name__)


class HistoriqueDao(metaclass=Singleton):
    pass