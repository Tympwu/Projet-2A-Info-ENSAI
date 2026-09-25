class utilisateur:
    def __init__(
        self,
        id : int,
        name : str,
        email : str,
        mot_de_passe : str,
        id_historique : int
    ) -> None :

        self.id: int = id
        self.name: str = name
        self.email: str = email
        self.mot_de_passe: str = mot_de_passe
        self.id_historique: int = id_historique
def __repr__(self) -> str:
        return f"Utilisateur(id={self.id}, name='{self.name}', email='{self.email}')"