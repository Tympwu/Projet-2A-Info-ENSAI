import datetime

from pydantic import BaseModel, EmailStr

from schema.fichier_model import FichierAuditModel


class DossierSchema(BaseModel):
    """
    Schéma de données pour les dossiers
    """

    nom: str
    chemin: str
    date_soumission: datetime.date | None = None
    liste_fichiers: list[FichierAuditModel] = []


class AuditModel(BaseModel):
    """Agit comme un modèle de données entre le frontend et le backend.

    Cela défini la struture JSON utilisé pour pour les échanges d'informations,
    assurant une forme de donnée constante et valide durant les échanges avec l'API
    """

    id: int | None = None
    name: str
    mot_de_passe: str
    email: EmailStr
    historique: str


class AuditReadModel(BaseModel):
    id: int | None = None
    score: float | None = None
    statut: str = "créé"
    date: datetime.date | None = None
    emissionCO2_total: float | None = None
    dossier: DossierSchema


class AuditHistoriqueModel(BaseModel):
    id: int
    statut: str
    score: float | None = None
