from pydantic import BaseModel, EmailStr, field_validator

from schema.audit_model import AuditReadModel


class HistoriqueSchema(BaseModel):
    """
    Format de l'historique utilisé par le formattage de l'utilisateur
    """

    id: int
    audits: list[AuditReadModel] = []


class UtilisateurModel(BaseModel):
    """Agit comme un modèle de données entre le frontend et le backend.

    Cela défini la struture JSON utilisé pour pour les échanges d'informations,
    assurant une forme de donnée constante et valide durant les échanges avec l'API
    """

    name: str
    mot_de_passe: str
    email: EmailStr | None = None

    @field_validator("mot_de_passe")
    @classmethod
    def check_password_length(cls, v: str) -> str:
        """Refuse les mots de passe de moins de 8 caractères."""
        min_len = 8
        if len(v) < min_len:
            raise ValueError(
                f"Le mot de passe doit être doit faire au minimum {min_len} caractères"
            )
        return v


class UtilisateurReadModel(BaseModel):
    """Utilisateur renvoyé par l'API (sans son mot de passe)."""

    id: int
    name: str
    email: EmailStr
    historique: HistoriqueSchema


class UtilisateurLoginModel(BaseModel):
    """Identifiants envoyés pour se connecter."""

    name: str
    mot_de_passe: str
