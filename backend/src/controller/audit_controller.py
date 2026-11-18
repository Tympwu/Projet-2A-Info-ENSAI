from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from schema.audit_model import AuditModel, AuditReadModel, DossierSchema
from service.audit_service import AuditService
from utils.log_utils import get_logger
from utils.security import preparer_contenu_hmac, verifier_hmac

print(">>> audit_controller chargé depuis :", __file__)

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


@router.post("/", response_model=AuditReadModel, tags=["Audits"])
async def create_audit(dossier, audit_service=Depends(get_audit_service)):
    """Créer un nouvel audit. Il faut au préalable avoir créé les fichiers contenu dans cet audit
    Args:
        dossier : Dossier contenant les fichiers à analyser.
        audit_service (AuditService): Le service utilisé pour intéragir avec les données de l'audit.
    Returns:
        AuditReadModel: Les données de l'audit nouvellement créé.
    Raises:
        HTTPException: Erreur 500 Erreur de lecture des fichiers.
        HTTPException: Erreur 500 Erreur d'analyse des anti-patterns
        HTTPException: Erreur 500 Erreur de calcul final des données
    """
    logger.info("Création d'un audit")
    print("hi")
    try:
        audit = audit_service.create_audit(dossier)
    except ValueError:
        raise HTTPException(status_code=500, detail="Erreur d'analyse des anti-patterns")
    except ArithmeticError:
        raise HTTPException(status_code=500, detail="Erreur de calcul final des données")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Erreur de lecture des fichiers.")

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
            raise HTTPException(
            status_code=400,
            detail="Nom de fichier manquant."
        )

        donnees = await fichier.read()
        fichiers_recus.append((fichier.filename, donnees))
    # 2. Reconstituer le contenu signé
    try:
        contenu = preparer_contenu_hmac(fichiers_recus)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))

    # 3. Vérifier la signature HMAC
    if not verifier_hmac(contenu, x_hmac_signature):
        raise HTTPException(
            status_code=403,
            detail="Signature HMAC invalide."
        )

    # 4. Restaurer les fichiers après lecture
    for fichier, (_, donnees) in zip(liste_fichier, fichiers_recus):
        fichier.file = BytesIO(donnees)

    # 5. Lancer le traitement uniquement si la signature est valide
    logger.info("Signature HMAC valide. Création du dossier.")

    dossier = audit_service.create_dossier(liste_fichier)
    audit = audit_service.create_audit(dossier)

    return audit