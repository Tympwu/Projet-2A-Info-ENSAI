# controller/historique_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.utilisateur_model import HistoriqueSchema
from service.historique_service import HistoriqueService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_historique_service():
    """Fonction permettant de récupérer les dépendances pour HistoriqueService"""
    return HistoriqueService()


@router.get("/", response_model=list[HistoriqueSchema], tags=["Historique"])
async def find_all_historique(historique_service=Depends(get_historique_service)):
    """Liste tous les historiques de la base de donnée.
    Returns:
        list[HistoriqueSchema]: Une liste de tous les historiques enregistrés.
    """
    logger.info("Liste tous les historiques")
    historique_list = historique_service.find_all_historiques()
    return historique_list


@router.get("/{id_utilisateur}", response_model=HistoriqueSchema, tags=["Historique"])
async def consulter_historique(
    id_utilisateur: int, historique_service=Depends(get_historique_service)
):
    """Trouve un historique en fonction de l'ID de son utilisateur.
    Args:
        id_utilisateur (int) : ID de l'utilisateur auquel appartient l'historique
        historique_service (HistoriqueService): Le service utilisé pour intéragir avec les données des historiques
    Returns:
        HistoriqueSchema: Les données de l'historique si trouvé
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé
        HTTPException: Erreur 500 si l'historique est introuvable
    """
    logger.info("Recherche d'un historique par ID de son utilisateur")
    try:
        historique = historique_service.consulter_historique(id_utilisateur)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Utilisateur (id={id_utilisateur}) not found.") from ValueError
    if not historique:
        raise HTTPException(status_code=500, details="Historique introuvable")
    return historique


@router.delete("/{id_utilisateur}", tags=["Historique"])
async def remove_historique(
    id_utilisateur: int, historique_service=Depends(get_historique_service)
):
    """Supprime un historique du système en se basant sur l'ID de son utilisateur.
    Args:
        id_utilisateur (int)
        historique_service (HistoriqueService): Le service utilisé pour intéragir avec les données des historiques.
    Returns:
        str: Un message de confirmation indiquant que l'historique a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Retrait d'un historique")
    try:
        success = historique_service.supprimer_historique(id_utilisateur)
    except ValueError:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'historique") from ValueError
    if not success:
        raise HTTPException(status_code=404, detail=f"Utilisateur(id={id_utilisateur}) introuvable")
    else:
        return "Historique supprimé"
