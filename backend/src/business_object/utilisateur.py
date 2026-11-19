from business_object.historique import Historique


class Utilisateur:
    def __init__(
        self,
        name: str,
        email: str,
        mot_de_passe: str,
        historique: Historique | None = None,
        id: int | None = None,
    ) -> None:

        self.id: int = id
        self.name: str = name
        self.email: str = email
        self.mot_de_passe: str = mot_de_passe
        self.historique: Historique | None = historique

    def __repr__(self) -> str:
        return f"Utilisateur(id={self.id}, name='{self.name}', email='{self.email}')"
