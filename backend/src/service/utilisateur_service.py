import hashlib
from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao
from utils.log_utils import get_logger, log

logger = get_logger(__name__)


class Utilisateur_service:
    """Classe de service gérant la logique métier liée aux utilisateurs."""

    def __init__(self) -> None:
        self.utilisateur_dao = UtilisateurDao()

    @log
    def verif_hash_mdp(self, mdp: str, name: str) -> str:
        """Génère le hash SHA-256 du mot de passe avec le nom comme sel."""
        salted_mdp = f"{name}{mdp}"
        return hashlib.sha256(salted_mdp.encode()).hexdigest()

    @log
    def connexion(self, hash_mdp: str, id_user: int) -> Utilisateur | None:
        """Vérifie le hash du mot de passe pour l'utilisateur spécifié."""
        utilisateur = self.utilisateur_dao.find_utilisateur(id_user)
        if utilisateur and utilisateur.mot_de_passe == hash_mdp:
            return utilisateur
        return None

    @log
    def create_utilisateur(self, hash_mdp: str, name: str) -> bool:
        """Crée un nouvel utilisateur en base de données[cite: 2]."""
        nouveau_user = Utilisateur(
            name=name, email="", mot_de_passe=hash_mdp
        )
        return self.utilisateur_dao.create_utilisateur(nouveau_user)

    @log
    def update_utilisateur(self, hash_mdp: str, name: str, id: int) -> bool:
        """Met à jour le nom et le mot de passe d'un utilisateur."""
        utilisateur = self.utilisateur_dao.find_utilisateur(id)
        if not utilisateur:
            return False

        utilisateur.name = name
        utilisateur.mot_de_passe = hash_mdp
        return self.utilisateur_dao.update(utilisateur)

    @log
    def remove_utilisateur(self, id: int) -> bool:
        """Supprime un utilisateur via son identifiant."""
        utilisateur = self.utilisateur_dao.find_utilisateur(id)
        if not utilisateur:
            return False

        return self.utilisateur_dao.delete(utilisateur)

    @log
    def find_utilisateur(self, id: int) -> Utilisateur:
        """Recherche et retourne un utilisateur par son ID."""
        return self.utilisateur_dao.find_utilisateur(id)

    @log
    def find_utilisateur_by_name(self, name: str) -> list[Utilisateur]:
        """Recherche les utilisateurs correspondant à un nom."""
        return self.utilisateur_dao.find_utilisateur_by_name(name)