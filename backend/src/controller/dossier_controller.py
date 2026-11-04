# controller/historique_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.fichier_model import FichierModel, FichierReadModel, FichierAuditModel
from schema.audit_model import DossierSchema
from service.dossier_service import DossierService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_dossier_service():
    """Fonction permettant de récupérer les dépendances pour HistoriqueService"""
    return DossierService()


@router.get("/", response_model=list[FichierReadModel], tags=["Fichier"])
async def find_all_fichier(dossier_service=Depends(get_dossier_service)):
    """Liste tous les fichiers de la base de donnée.
    Args:
        dossier_service (DossierService): Service utilisé pour intéragir avec les données des fichiers et dossiers
    Returns:
        list[FichierReadModel]: Une liste de tous les fichiers enregistrés.
    """
    logger.info("Liste tous les fichiers")
    fichier_list = dossier_service.find_all_fichier()
    return fichier_list


@router.get("/{id_fichier}", response_model=FichierReadModel, tags=["Fichier"])
async def find_fichier(id_fichier: int, dossier_service=Depends(get_dossier_service)
):
    """Trouve un fichier en fonction de son ID.
    Args:
        id_fichier (int) : ID de l'utilisateur auquel appartient l'historique
        dossier_service (DossierService): Le service utilisé pour interagir avec les données des fichiers et dossiers
    Returns:
        FichierReadModel: Les données du fichier si trouvé
    Raises:
        HTTPException: Erreur 404 si le fichier n'est pas trouvé
    """
    logger.info("Recherche d'un fichier par son ID")
    fichier = dossier_service.find_fichier_by_id(id_fichier)
    if not fichier:
        raise HTTPException(status_code=500, details="Fichier introuvable")
    return fichier


@router.delete("/{id_fichier}", tags=["Fichier"])
async def remove_fichier(
    id_fichier: int, dossier_service=Depends(get_dossier_service)
):
    """Supprime un fichier du système en se basant sur son ID.
    Args:
        id_fichier (int)
        dossier_service (DossierService): Le service utilisé pour intéragir avec les données des dossiers et fichiers.
    Returns:
        str: Un message de confirmation indiquant que le fichier a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si le fichier n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Retrait d'un fichier")
    try:
        success = dossier_service.delete_fichier(id_fichier)
    except ValueError:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'historique")
    if not success:
        raise HTTPException(status_code=404, detail=f"Fichier(id={id_fichier}) introuvable")
    else:
        return "Fichier supprimé"

"""
+ create_dossier(fichiers : Fichier)
+ remove_dossier(chemin_dossier : str)
+ update_dossier(chemin_dossier : str)
+ read_dossier(chemin_dossier : str)
+ update_fichier(id_fichier : int, fichier : Fichier)
+ find_by_utilisateur(id_utilisateur : int)
"""