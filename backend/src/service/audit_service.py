import shutil
import tempfile
import zipfile
from pathlib import Path

from business_object.audit import Audit
from business_object.fichier import Fichier
from dao.audit_dao import AuditDao
from service.dossier_service import DossierService
from utils.log_utils import log

TAILLE_MAX_ZIP = 50 * 1024 * 1024  # 50 Mo décompressés (protection contre les zip bombs)


class AuditService:
    """Gère la consultation et la suppression de l'audit d'un utilisateur."""

    def __init__(self):
        """
        Parameters:
            audit_dao (AuditDao) : Classe DAO spécifique aux audits
            dossier_service (DossierService): Classe Service spécifique aux dossiers
        """
        self.audit_dao = AuditDao()
        self.dossier_service = DossierService()

    @log
    def find_audit(self, id_audit: int) -> Audit | None:
        """Retourne un audit spécifique.

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            Audit | None: L'audit demandé, None si ce dernier n'a pas été trouvé.
        """
        audit = self.audit_dao.find_audit(id_audit)
        return audit

    @log
    def create_audit(self, chemin_dossier: str) -> Audit:
        """Créer un audit en se basant sur le chemin d'accès du dossier

        Args:
            chemin_dossier (str): Chemin d'accès du dossier contenant les fichiers.

        Returns:
            Audit: L'audit nouvellement crée, None si il y a eu un échec dans la création.
        Raises:
            ValueError: Le chemin indiqué ne mène à aucun dossier
        """
        dossier = self.dossier_service.consulter_dossier(chemin_dossier)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return self.dossier_service.traiter_dossier(dossier)

    @log
    def remove_audit(self, id_audit: int) -> bool:
        """Supprime un audit spécifié via son ID.

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            bool: True si la suppression à réusie, False sinon
        """
        audit = self.find_audit(id_audit)
        if not audit:
            return False
        return self.audit_dao.remove_audit(audit)

    @log
    def find_all_audit(self) -> list[Audit]:
        """Renvoie tous les audits de la base de données.
        Returns:
            list[Audit]: Liste composée de tous les audits enregistrés. La liste est vide si aucun audit est trouvé"""
        return self.audit_dao.find_all()

    @log
    def create_dossier(self, liste_fichier) -> Audit:
        """Écrit les fichiers reçus dans un dossier temporaire (en dézippant les .zip),
        puis lance l'audit sur ce dossier.

        Args:
            liste_fichier (list[UploadFile]): Fichiers envoyés par le client.

        Returns:
            Audit: L'audit calculé sur le dossier.

        Raises:
            zipfile.BadZipFile: Si une archive .zip est invalide.
            ValueError: Si une archive est trop volumineuse ou si le dossier est introuvable.
        """
        dossier_temp = Path(tempfile.mkdtemp(prefix="audit_"))
        try:
            for fichier in liste_fichier:
                nom = Path(fichier.filename).name  # .name évite les chemins du type "../x"
                if nom.lower().endswith(".zip"):
                    self._extraire_zip(fichier.file, dossier_temp)
                else:
                    with open(dossier_temp / nom, "wb") as sortie:
                        shutil.copyfileobj(fichier.file, sortie)
            for chemin in sorted(p for p in dossier_temp.rglob("*") if p.is_file()):
                if not self.dossier_service.create_fichier(Fichier(chemin=str(chemin))):
                    raise ValueError(f"Impossible d'enregistrer le fichier {chemin.name}")

            return self.create_audit(str(dossier_temp))
        except Exception:
            # En cas d'échec, on ne laisse pas un dossier temporaire orphelin
            shutil.rmtree(dossier_temp, ignore_errors=True)
            raise

    def _extraire_zip(self, flux, destination: Path) -> None:
        """Extrait une archive zip dans le dossier de destination, de façon sécurisée."""
        racine = destination.resolve()
        total = 0
        with zipfile.ZipFile(flux) as archive:
            for info in archive.infolist():
                if info.is_dir() or "__MACOSX" in info.filename:
                    continue

                total += info.file_size
                if total > TAILLE_MAX_ZIP:
                    raise ValueError("Archive trop volumineuse")

                cible = (racine / info.filename).resolve()
                # Zip slip : on ignore tout chemin qui sortirait du dossier de destination
                if racine not in cible.parents:
                    continue

                cible.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, open(cible, "wb") as sortie:
                    shutil.copyfileobj(source, sortie)
