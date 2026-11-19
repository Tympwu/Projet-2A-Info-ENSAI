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

    code: str
    extension: str
    complexite: int | None = None
    score: float | None = None
    emissionCO2: float | None = None

    @field_validator("extension")
    @classmethod
    def check_extension(cls, v: str) -> str:
        if v not in {".py", ".lock", ".txt", ".toml"}:
            raise TypeError("Le type de fichier accepté doit être un .py, .txt, .toml ou .lock")
        return v

    @field_validator("complexite")
    @classmethod
    def check_complexite(cls, v: int) -> int:
        if v is None:
            return v
        elif not isinstance(v, int):
            raise ValueError("Le format de complexité n'est pas le bon")
        return v


class FichierReadModel(BaseModel):
    id: int
    code: str
    extension: str
    complexite: int | None = None
    score: float | None = None
    emissionCO2: float | None = None


class FichierSubmitModel(BaseModel):
    code: str
    extension: str
    complexite: int | None = None
    score: float | None = None
    emissionCO2: int | None = None

    @field_validator("extension")
    @classmethod
    def check_extension(cls, v: str) -> str:
        if v not in {".py", ".lock", ".txt"}:
            raise TypeError("Le type de fichier accepté doit être un .py, .txt ou .lock")
        return v
