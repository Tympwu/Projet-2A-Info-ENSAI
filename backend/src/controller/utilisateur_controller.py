# controller/utilisateur_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.utilisateur_model import UtilisateurModel, UtilisateurReadModel
from service.utilisateur_service import UtilisateurService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_utilisateur_service():
    """Fonction permettant de récupérer les dépendances pour Utilisateur_service"""
    return UtilisateurService()


@router.get("/", response_model=list[UtilisateurReadModel], tags=["Utilisateurs"])
async def find_all_utilisateurs(utilisateur_service=Depends(get_utilisateur_service)):
    """Liste tous les utilisateurs.
    Returns:
        list[UtilisateurReadModel]: Une liste de tous les utilisateurs enregistrés.
    """
    logger.info("Liste tous les utilisateurs")
    utilisateur_list = utilisateur_service.find_all()
    return utilisateur_list


@router.get("/{id_utilisateur}", response_model=UtilisateurReadModel, tags=["Utilisateurs"])
async def find_utilisateur(
    id_utilisateur: int, utilisateur_service=Depends(get_utilisateur_service)
):
    """Trouve un utilisateur en fonction de son ID.
    Args:
        id_utilisateur (int)
        utilisateur_service (UtilisateurService): Le service utilisé pour intéragir avec les données de l'utilisateur
    Returns:
        UtilisateurReadModel: Les données de l'utilisateur si trouvé
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé
    """
    logger.info("Recherche d'un utilisateur par ID")
    utilisateur = utilisateur_service.find_utilisateur(id_utilisateur)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur (id={id_utilisateur}) not found.")
    return utilisateur


@router.post("/", response_model=UtilisateurReadModel, tags=["Utilisateurs"])
async def create_player(u: UtilisateurModel, utilisateur_service=Depends(get_utilisateur_service)):
    """Créer un nouvel utilisateur.
    Args:
        u (UtilisateurReadModel): Les données de l'utilisateur à créer.
        utilisateur_service (UtilisateurService): Le service utilisé pour intéragir avec les données de l'utilisateur.
    Returns:
        UtilisateurReadModel: Les données de l'utilisateur nouvellement créé.
    Raises:
        HTTPException: 500 error s'il y a une erreur de création.
    """
    logger.info("Création d'un utilisateur")
    player = utilisateur_service.create_utilisateur(u.name, u.mot_de_passe, u.email)
    if not player:
        raise HTTPException(status_code=500, detail="Erreur lors de la création.")

    return player


@router.put("/{id_utilisateur}", response_model=UtilisateurReadModel, tags=["Utilisateurs"])
async def update_player(
    id_utilisateur: int, u: UtilisateurModel, utilisateur_service=Depends(get_utilisateur_service)
):
    """Met à jour un utilisateur.
    Args:
        id_utilisateur (int)
        u (UtilisateurModel): Les nouvelles données pour l'utilisateur.
        utilisateur_service (UtilisateurService): Le service utilisé pour mettre à jour les données de l'utilisateurs.
    Returns:
        UtilisateurReadModel: Les nouvelles données de l'utilisateur.
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé.
        HTTPException: Erreur 500 si le processus de mise à jour rate.
    """
    logger.info("Mise à jour d'un utilisateur")
    utilisateur = utilisateur_service.find_utilisateur(id_utilisateur)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur (id={id_player}) introuvable.")

    utilisateur = utilisateur_service.update_utilisateur(id_utilisateur, u.name, u.mot_de_passe, u.email)
    if not utilisateur:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour des données.")

    return utilisateur


@router.delete("/{id_utilisateur}", tags=["Utilisateurs"])
async def delete_player(id_utilisateur: int, utilisateur_service=Depends(get_utilisateur_service)):
    """Delete a player from the system.
    Args:
        id_player (int)
        utilisateur_service (PlayerService): The service used to interact with player data.
    Returns:
        str: A confirmation message indicating the player was deleted.
    Raises:
        HTTPException: 404 error if the player is not found.
    """
    logger.info("Delete a player")
    player = utilisateur_service.find_by_id(id_player)
    if not player:
        raise HTTPException(status_code=404, detail="Player (id={id_player}) not found.")

    utilisateur_service.delete(player)
    return f"Player {player.username} deleted"
