# controller/utilisateur_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.player_model import PlayerModel, PlayerReadModel
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
    utilisateur = utilisateur_service.find_by_id(id_utilisateur)
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


@router.put("/{id_player}", response_model=PlayerReadModel, tags=["Utilisateurs"])
async def update_player(
    id_player: int, p: PlayerModel, utilisateur_service=Depends(get_utilisateur_service)
):
    """Update an existing player's information.
    Args:
        id_player (int)
        p (PlayerModel): The new data for the player.
        utilisateur_service (PlayerService): The service used to interact with player data.
    Returns:
        str: A confirmation message indicating the player was updated.
    Raises:
        HTTPException: 404 error if the player is not found.
        HTTPException: 500 error if the update process fails.
    """
    logger.info("Update a player")
    player = utilisateur_service.find_by_id(id_player)
    if not player:
        raise HTTPException(status_code=404, detail="Player (id={id_player}) not found.")

    player.username = p.username
    player.password = p.password
    player.elo = p.elo
    player.email = p.email
    player.pokemon_fan = p.pokemon_fan

    player = utilisateur_service.update(player)
    if not player:
        raise HTTPException(status_code=500, detail="Error while updating player.")

    return player


@router.delete("/{id_player}", tags=["Utilisateurs"])
async def delete_player(id_player: int, utilisateur_service=Depends(get_utilisateur_service)):
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
