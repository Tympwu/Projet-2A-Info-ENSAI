# controller/historique_controller.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from business_object.dossier import Dossier
from business_object.fichier import Fichier
from schema.audit_model import DossierSchema, DossierSubmitSchema
from schema.fichier_model import FichierReadModel, FichierSubmitModel
from service.dossier_service import DossierService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_dossier_service():
    """Fonction permettant de récupérer les dépendances pour HistoriqueService"""
    return DossierService()


@router.get("/fichier", response_model=list[FichierReadModel], tags=["Fichier"])
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


@router.get("/fichier/{id_fichier}", response_model=FichierReadModel, tags=["Fichier"])
async def find_fichier(id_fichier: int, dossier_service=Depends(get_dossier_service)):
    """Trouve un fichier en fonction de son ID.
    Args:
        id_fichier (int) : ID du fichier recherché
        dossier_service (DossierService): Le service utilisé pour interagir avec les données des fichiers et dossiers
    Returns:
        FichierReadModel: Les données du fichier si trouvé
    Raises:
        HTTPException: Erreur 404 si le fichier n'est pas trouvé
    """
    logger.info("Recherche d'un fichier par son ID")
    fichier = dossier_service.find_fichier_by_id(id_fichier)
    if not fichier:
        raise HTTPException(status_code=500, detail="Fichier introuvable")
    return fichier


@router.delete("/fichier/{id_fichier}", tags=["Fichier"])
async def remove_fichier(id_fichier: int, dossier_service=Depends(get_dossier_service)):
    """Supprime un fichier du système en se basant sur son ID.
    Args:
        id_fichier (int)
        dossier_service (DossierService): Le service utilisé pour intéragir avec les données des dossiers et fichiers.
    Returns:
        str: Un message de confirmation indiquant que le fichier a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si le fichier n'est pas trouvé.
    """
    logger.info("Retrait d'un fichier")
    success = dossier_service.remove_fichier(id_fichier)
    if not success:
        raise HTTPException(status_code=404, detail=f"Fichier(id={id_fichier}) introuvable")
    else:
        return "Fichier supprimé"


@router.post("/fichier", response_model=FichierReadModel, tags=["Fichier"])
async def create_fichier(fichier: FichierSubmitModel, dossier_service=Depends(get_dossier_service)):
    """Créer un fichier
    Args:
        fichier (FichierSubmitModel): Données du fichier à créer
        dossier_service (DossierService): Service permettant d'intéragir avec les données des fichiers et dossiers
    Returns:
        FichierReadModel : Fichier créé
    Raises:
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Création d'un fichier")
    nouv_fichier = dossier_service.create_fichier(
        Fichier(chemin=fichier.chemin, extension=fichier.extension)
    )
    if nouv_fichier is None:
        raise HTTPException(status_code=500, detail="Echec de la création du fichier")
    else:
        return nouv_fichier


@router.post("/fichier/{id_fichier}", response_model=FichierReadModel, tags=["Fichier"])
async def update_fichier(
    id_fichier: int, fichier: FichierSubmitModel, dossier_service=Depends(get_dossier_service)
):
    """Met à jour un fichier du système en se basant sur son ID
    Args:
        id_fichier (int): ID du fichier à mettre à jour
        fichier (FichierModel): Données utilisées pour mettre à jour le fichier voulu
    Returns:
        FichierReadModel : Fichier avec les données mise à jour
    Raises:
        HTTPException: Erreur 404 si le fichier n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Mise à jour d'un fichier")
    fichier_init = dossier_service.find_fichier_by_id(id_fichier)
    if not fichier_init:
        raise HTTPException(status_code=404, detail=f"Fichier (id={id_fichier}) introuvable.")

    fichier_nouv = dossier_service.update_fichier(
        Fichier(
            chemin=fichier.chemin,
            id=id_fichier,
            extension=fichier.extension,
            complexite=fichier.complexite,
            emissionCO2=fichier.emissionCO2,
            score=fichier.score,
        )
    )
    if not fichier_nouv:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la mise à jour des données. Potentiellement le fichier à déjà été analysé et ne peut pas être modifié dans ce cas.",
        )

    return fichier_nouv


@router.get(
    "/fichier_by_user/{id_utilisateur}", response_model=list[FichierReadModel], tags=["Fichier"]
)
async def find_by_utilisateur(id_utilisateur: int, dossier_service=Depends(get_dossier_service)):
    """Trouve une liste de fichiers en fonction de l'ID d'un utilisateur.
    Args:
        id_utilisateur (int) : ID de l'utilisateur pour lequel on désire la liste des fichiers
        dossier_service (DossierService): Le service utilisé pour interagir avec les données des fichiers et dossiers
    Returns:
        list[FichierReadModel]: Les données des fichiers si trouvés
    Raises:
        HTTPException: Erreur 404 si l'utilisateur n'est pas trouvé
    """
    logger.info("Recherche de fichiers par ID d'utilisateur")
    fichiers = dossier_service.find_fichier_by_user(id_utilisateur)
    if fichiers is None:
        raise HTTPException(status_code=500, detail="Utilisateur introuvable")
    return fichiers


@router.delete("/dossier/{chemin_dossier}", tags=["Dossier"])
async def remove_dossier(chemin_dossier: str, dossier_service=Depends(get_dossier_service)):
    """Supprime un dossier du système et ce qu'il contient en se basant sur son chemin d'accès.
    Args:
        chemin_dossier (str)
        dossier_service (DossierService): Le service utilisé pour intéragir avec les données des dossiers et fichiers.
    Returns:
        str: Un message de confirmation indiquant que le dossier a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si le dossier n'est pas trouvé.
    """
    logger.info("Retrait d'un dossier")
    success = dossier_service.remove_dossier(chemin_dossier)
    if not success:
        raise HTTPException(status_code=404, detail=f"Dosser(path={chemin_dossier}) introuvable")
    else:
        return "Dossier supprimé"


@router.post("/dossier/{chemin_dossier}", response_model=DossierSchema, tags=["Dossier"])
async def update_dossier(
    chemin_dossier: str, dossier: DossierSubmitSchema, dossier_service=Depends(get_dossier_service)
):
    """Met à jour un dossier du système en se basant sur son chemin d'accès
    Args:
        chemin_dossier (str): chemin d'accès du dossier à mettre à jour
        dossier (DossierSubmitSchema): Données utilisées pour mettre à jour le dossier voulu
        dossier_service (DossierService): Service permettant de manipuler les données liés aux dossiers
    Returns:
        DossierSchema : Dossier avec les données mise à jour
    Raises:
        HTTPException: Erreur 404 si le dossier n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Mise à jour d'un dossier")
    dossier_init = dossier_service.consulter_dossier(chemin_dossier)
    if not dossier_init:
        raise HTTPException(status_code=404, detail=f"Dossier (path={chemin_dossier}) introuvable.")

    dossier_nouv = dossier_service.update_dossier(
        chemin_dossier,
        Dossier(
            nom=dossier.nom,
            chemin=dossier.chemin,
            liste_fichiers=dossier.liste_fichiers,
            date_soumission=datetime.today(),
        ),
    )
    if not dossier_nouv:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la mise à jour des données. Potentiellement le dossier à déjà été analysé et ne peut pas être modifié dans ce cas.",
        )

    return dossier_nouv


@router.get("/dossier/{chemin_dossier}", response_model=DossierSchema, tags=["Dossier"])
async def read_dossier(chemin_dossier: str, dossier_service=Depends(get_dossier_service)):
    """Trouve un dossier en fonction de son chemin d'accès.
    Args:
        chemin_dossier (str) : chemin d'accès du dossier recherché
        dossier_service (DossierService): Le service utilisé pour interagir avec les données des fichiers et dossiers
    Returns:
        DossierSchema: Les données du fichier si trouvé
    Raises:
        HTTPException: Erreur 404 si le dossier n'est pas trouvé
    """
    logger.info("Recherche d'un dossier par son ID")
    dossier = dossier_service.consulter_dossier(chemin_dossier)
    if not dossier:
        raise HTTPException(status_code=500, detail="Dossier introuvable")
    return dossier
