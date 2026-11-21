import datetime

from pydantic import BaseModel

from schema.fichier_model import FichierReadModel, FichierSubmitModel


class DossierSubmitSchema(BaseModel):
    """
    Schéma de données pour la submission de dossier
    """

    nom: str
    liste_fichiers: list[FichierSubmitModel]


class DossierSchema(BaseModel):
    """
    Schéma de données pour les dossiers
    """

    nom: str
    date_soumission: datetime.datetime | None = None
    liste_fichiers: list[FichierReadModel] = []


class AuditModel(BaseModel):
    """Agit comme un modèle de données entre le frontend et le backend.

    Cela défini la struture JSON utilisé pour pour les échanges d'informations,
    assurant une forme de donnée constante et valide durant les échanges avec l'API
    """

    statut: str = "créé"
    liste_fichier: list[int]


class AuditReadModel(BaseModel):
    id: int | None = None
    score: float | None = None
    statut: str = "créé"
    date: datetime.datetime | None = datetime.datetime.today()
    emissionCO2_total: float | None = None
    dossier: DossierSchema
    complexite_total: int | None = None


class AuditHistoriqueModel(BaseModel):
    id: int
    statut: str
    score: float | None = None


class CertificatModel(BaseModel):
    """Certificat renvoyé par l'API après application de la Quality Gate (F5)."""

    audit_id: int
    nom: str
    date_delivrance: datetime.datetime | None = None
    statut: str
    score: float | None = None
    emissionCO2_total: float | None = None
    motifs: list[str] = []
    cle: bytes


class SignatureRequest(BaseModel):
    """Signature contenu dans un certificat"""
    signature: str
    id_audit: int
    date_delivrance: datetime.datetime
