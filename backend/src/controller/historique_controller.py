# controller/historique_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.utilisateur_model import HistoriqueSchema
from schema.audit_model import AuditHistoriqueModel, AuditReadModel, AuditModel
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
        raise HTTPException(status_code=404, detail="Utilisateur (id={id_utilisateur}) not found.")
    if not historique:
        raise HTTPException(status_code=500, details="Historique introuvable")
    return historique


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
        raise HTTPException(status_code=404, detail="Utilisateur (id={id_player}) introuvable.")

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
            status_code=404, detail="Utilisateur (id={id_utilisateur}) introuvable."
        )

    success = utilisateur_service.remove_utilisateur(id_utilisateur)
    if not success:
        raise HTTPException(
            status_code=500, detail="Erreur lors de la suppression de l'utilisateur"
        )
    else:
        return f"Player {utilisateur.name} deleted"


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
