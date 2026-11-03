import hashlib

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao
from service.historique_service import Historique_service
from utils.log_utils import get_logger, log
from utils.security import hash_password

logger = get_logger(__name__)


class UtilisateurService:
    """Classe de service gérant la logique métier liée aux utilisateurs."""

    def __init__(self) -> None:
        self.utilisateur_dao = UtilisateurDao()

    @log
    def verif_hash_mdp(self, mdp: str, name: str) -> str:
        """Génère le hash SHA-256 du mot de passe avec le nom comme sel."""
        salted_mdp = f"{name}{mdp}"
        return hashlib.sha256(salted_mdp.encode()).hexdigest()

    @log
    def connexion(self, name: str, mdp: str) -> Utilisateur | None:
        """Permet de connecter un utilisateur en vérifiant son nom et son mot de passe haché."""
        hash_mdp = self.verif_hash_mdp(mdp, name)
        # On utilise directement la méthode login_utilisateur du DAO
        return self.utilisateur_dao.login_utilisateur(name, hash_mdp)

    @log
    def create_utilisateur(self, name: str, mot_de_passe: str, email: str) -> bool:
        """Crée un nouvel utilisateur en base de données."""
        nouveau_user = Utilisateur(
            name=name, email=email, mot_de_passe=hash_password(mot_de_passe, name)
        )
        if self.utilisateur_dao.create_utilisateur(nouveau_user):
            nouveau_user.historique = Historique_service().create_historique(nouveau_user.id)
            return nouveau_user
        return None

    @log
    def update_utilisateur(self, id: int, name: str, mdp: str, email: str) -> bool:
        """Met à jour les informations d'un utilisateur."""
        utilisateur = self.utilisateur_dao.find_utilisateur(id)
        if not utilisateur:
            return False

        hash_mdp = self.verif_hash_mdp(mdp, name)
        utilisateur.name = name
        utilisateur.mot_de_passe = hash_mdp
        utilisateur.email = email

        return utilisateur if self.utilisateur_dao.update_utilisateur(utilisateur) else None

    @log
    def remove_utilisateur(self, id: int) -> bool:
        """Supprime un utilisateur via son identifiant."""
        utilisateur = self.utilisateur_dao.find_utilisateur(id)
        if not utilisateur:
            return False

        return self.utilisateur_dao.remove_utilisateur(utilisateur)

    @log
    def find_utilisateur(self, id: int) -> Utilisateur | None:
        """Recherche et retourne un utilisateur par son ID."""
        return self.utilisateur_dao.find_utilisateur(id)

    @log
    def find_utilisateur_by_name(self, name: str) -> list[Utilisateur]:
        """Recherche les utilisateurs correspondant à un nom."""
        return self.utilisateur_dao.find_utilisateur_by_name(name)

    @log
    def find_all(self) -> list[Utilisateur]:
        """Renvoie tous les utilisateurs de la base de données."""
        return self.utilisateur_dao.find_all()
