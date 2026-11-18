from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from schema.audit_model import AuditReadModel
from service.audit_service import AuditService
from utils.log_utils import get_logger
from utils.security import preparer_contenu_hmac, verifier_hmac

router = APIRouter()

logger = get_logger(__name__)


def get_audit_service():
    """Fonction permettant de récupérer les dépendances pour AuditService"""
    return AuditService()


@router.get("/", response_model=list[AuditReadModel], tags=["Audits"])
async def find_all_audit(audit_service=Depends(get_audit_service)):
    """Liste tous les audits.
    Returns:
        list[AuditReadModel]: Une liste de tous les audits enregistrés.
    """
    logger.info("Liste tous les audits")
    audit_list = audit_service.find_all_audit()
    return audit_list


@router.get("/{id_audit}", response_model=AuditReadModel, tags=["Audits"])
async def consulter_audit(id_audit: int, audit_service=Depends(get_audit_service)):
    """Trouve un audit en fonction de son ID.
    Args:
        id_audit (int)
        audit_service (AuditReadModel): Le service utilisé pour intéragir avec les données des audits
    Returns:
        AuditReadModel: Les données de l'audit si trouvé
    Raises:
        HTTPException: Erreur 404 si l'audit n'est pas trouvé
    """
    logger.info("Recherche d'un audit par ID")
    audit = audit_service.find_audit(id_audit)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit (id={id_audit}) not found.")
    return audit


@router.delete("/{id_audit}", tags=["Audits"])
async def remove_audit(id_audit: int, audit_service=Depends(get_audit_service)):
    """Supprime un audit du système.
    Args:
        id_audit (int)
        audit_service (AuditService): Le service utilisé pour intéragir avec les données de l'audit.
    Returns:
        str: Un message de confirmation indiquant que l'audit a bien été supprimé.
    Raises:
        HTTPException: Erreur 404 si l'audit n'est pas trouvé.
        HTTPException: Erreur 500 si le processus échoue
    """
    logger.info("Retrait d'un audit")
    audit = audit_service.find_audit(id_audit)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit (id={id_audit}) introuvable.")

    success = audit_service.remove_audit(id_audit)
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'audit")
    else:
        return f"Audit {audit.id} supprimé"


@router.post("/start_audit", tags=["Audits"])
async def start_audit(
    liste_fichier: list[UploadFile] = File(...),
    utilisateur_id: int | None = Form(None),
    x_hmac_signature: str = Header(..., alias="X-HMAC-Signature"),
    audit_service=Depends(get_audit_service),
):
    """F1 : Vérifier la signature HMAC avant de lancer l'audit."""

    fichiers_recus = []

    # 1. Lire les fichiers envoyés par le frontend
    for fichier in liste_fichier:
        if not fichier.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

        donnees = await fichier.read()
        fichiers_recus.append((fichier.filename, donnees))
    # 2. Reconstituer le contenu signé
    try:
        contenu = preparer_contenu_hmac(fichiers_recus)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from ValueError

    # 3. Vérifier la signature HMAC
    if not verifier_hmac(contenu, x_hmac_signature):
        raise HTTPException(status_code=403, detail="Signature HMAC invalide.")

    # 4. Restaurer les fichiers après lecture
    for fichier, (_, donnees) in zip(liste_fichier, fichiers_recus, strict=False):
        fichier.file = BytesIO(donnees)

    # 5. Lancer le traitement uniquement si la signature est valide
    logger.info("Signature HMAC valide. Création du dossier.")

    dossier = audit_service.create_dossier(liste_fichier)
    audit = audit_service.create_audit(dossier)

    return audit


@router.post("/detail_audit", tags=["Audits"])
async def detail_audit(taille_entree: int = 500, audit_service=Depends(get_audit_service)):
    """Continue l'analyse de l'audit en proposant une analyse de la complexité et de l'émission de CO2
    Args
    ----
        taille_entree (int) : Taille de l'entrée utilisé pour estimer les emissions de CO2
        audit_service (AuditService) : Service utilisé pour intéragir avec les données de l'audit
    Raises
    ------
        HTTPException: Erreur 500 si l'audit ne peut pas être analysé
    Returns
    -------
        Audit : Audit analysé vis-à-vis de la complexité et de l'émission
    """
    try:
        audit = audit_service.analyse_CO2_audit(nb_entree=taille_entree)
    except ValueError:
        raise HTTPException(status_code=500, detail="Erreur lors de l'analyse.\nCela peut provenir d'une absence d'audit en mémoire, de fichiers incompatibles ou d'erreur d'analyse.") from ValueError
    return audit
