from pydantic import BaseModel, field_validator


class VulnerabiliteSchema(BaseModel):
    """
    Schéma de données pour les vulnérabilités
    """

    description: str
    score_danger: int


class DependanceSchema(BaseModel):
    """
    Schéma de données pour les dépendances
    """

    nom: str
    auteur: str
    version: str


class FichierModel(BaseModel):
    """Agit comme un modèle de données entre le frontend et le backend.

    Cela défini la struture JSON utilisé pour pour les échanges d'informations,
    assurant une forme de donnée constante et valide durant les échanges avec l'API
    """

    id: int | None = None
    chemin: str
    extension: str
    complexite: str | None = None
    score: int | None = None
    emissionCO2: float | None = None
    liste_vulnerabilites: list[VulnerabiliteSchema] = []
    liste_dependances: list[DependanceSchema] = []

    @field_validator("extension")
    @classmethod
    def check_extension(cls, v: str) -> str:
        if v not in {".py", ".lock", ".txt"}:
            raise TypeError("Le type de fichier accepté doit être un .py ou un .lock")
        return v

    @field_validator("complexite")
    @classmethod
    def check_complexite(cls, v: str) -> str:
        if len(v) != len("O(n^p)") or v[:4] != "O(n^":
            raise ValueError("Le format de complexité n'est pas le bon")
        return v


class FichierReadModel(BaseModel):
    id: int
    chemin: str
    extension: str
    complexite: str | None = None
    score: int | None = None
    emissionCO2: float | None = None


class FichierAuditModel(BaseModel):
    chemin: str
    extension: str
    complexite: str | None = None
    score: int | None = None
    emissionCO2: float | None = None
