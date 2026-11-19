# controller/utilisateur_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.utilisateur_model import UtilisateurLoginModel, UtilisateurModel, UtilisateurReadModel
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
    utilisateur_list = utilisateur_service.find_all_utilisateurs()
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
        raise HTTPException(
            status_code=404, detail=f"Utilisateur (id={id_utilisateur}) introuvable."
        )
    return utilisateur


@router.post("/", response_model=UtilisateurReadModel, tags=["Utilisateurs"])
async def create_utilisateur(
    u: UtilisateurModel, utilisateur_service=Depends(get_utilisateur_service)
):
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
async def update_utilisateur(
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
        raise HTTPException(
            status_code=404, detail=f"Utilisateur (id={id_utilisateur}) introuvable."
        )

    utilisateur = utilisateur_service.update_utilisateur(
        id_utilisateur, u.name, u.mot_de_passe, u.email
    )
    if not utilisateur:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour des données.")

    return utilisateur


@router.delete("/{id_utilisateur}", tags=["Utilisateurs"])
async def remove_utilisateur(
    id_utilisateur: int, utilisateur_service=Depends(get_utilisateur_service)
):
    """Supprime un utilisateur du système.
    Args:
        id_utilisateur (int)
        utilisateur_service (UtilisateurService): Le service utilisé pour intéragir avec les données de l'utilisateur.
    Returns:
        str: Un message de confirmation indiquant que l'utilisateur a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Retrait un utilisateur")
    utilisateur = utilisateur_service.find_utilisateur(id_utilisateur)
    if not utilisateur:
        raise HTTPException(
            status_code=404, detail=f"Utilisateur (id={id_utilisateur}) introuvable."
        )

    success = utilisateur_service.remove_utilisateur(id_utilisateur)
    if not success:
        raise HTTPException(
            status_code=500, detail="Erreur lors de la suppression de l'utilisateur"
        )
    else:
        return f"Utilisateur {utilisateur.name} supprimé"


@router.post("/login", response_model=UtilisateurReadModel, tags=["Utilisateurs"])
def login(credentials: UtilisateurLoginModel, service=Depends(get_utilisateur_service)):
    """Identifie un utilisateur.
    Args:
        credentials: nom et mot de passe.
    Returns:
        UtilisateurReadModel: Les données intéressantes de l'utilisateur connecté
    Raises:
        HTTPException: Erreur 401 si les informations sont incorrectes ou l'utilisateur n'existe pas."""
    logger.info("Login")
    utilisateur = service.login(credentials.name, credentials.mot_de_passe)
    if utilisateur:
        return utilisateur
    raise HTTPException(status_code=401, detail="Invalid credentials")
