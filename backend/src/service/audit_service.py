import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from business_object.audit import Audit
from business_object.certificat import Certificat
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from business_object.sbom import SBOM
from dao.audit_dao import AuditDao
from service.analyse_fichier import Analyse_fichier
from service.dossier_service import DossierService
from utils.log_utils import log
from utils.security import decrypt_certificat
from utils.singleton import Singleton

EXTENSIONS_AUTORISEES = {".py", ".txt", ".toml", ".lock"}
TAILLE_MAX_ZIP = 50 * 1024 * 1024  # 50 Mo décompressés (protection contre les zip bombs)


class AuditService(metaclass=Singleton):
    """Gère la consultation et la suppression de l'audit d'un utilisateur."""

    def __init__(self):
        """
        Parameters:
            audit_dao (AuditDao) : Classe DAO spécifique aux audits
            dossier_service (DossierService): Classe Service spécifique aux dossiers
        """
        self.audit_dao = AuditDao()
        self.dossier_service = DossierService()
        self.analyse_fichier = Analyse_fichier()
        self.current_audit = None

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
    def create_audit(self, dossier, nb_entree) -> Audit:
        """Créer un audit en se basant sur le dossier contenu dans l'audit

        Args:
            dossier (Dossier): Dossier contenant tous les fichiers
            nb_entree (int): Taille de l'entrée à utiliser pour calculer les émissions

        Returns:
            Audit: L'audit nouvellement crée, None si il y a eu un échec dans la création.
        Raises:
            ValueError: Le chemin indiqué ne mène à aucun dossier
        """
        if not dossier:
            raise ValueError("Dossier introuvable")
        self.current_audit = self.dossier_service.traiter_dossier(dossier)
        self.current_audit = self.dossier_service.traiter_emission_dossier(
            self.current_audit, nb_entree
        )
        self.current_audit.calculer_complexite()
        return self.current_audit

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
    def create_dossier(self, liste_fichier) -> Audit | None:
        """Lit les fichiers reçus (dézippe les .zip), construit un Dossier en mémoire
        puis lance l'audit dessus.

        Args:
            liste_fichier (list[UploadFile]): Fichiers envoyés par le client.

        Returns:
            Audit | None: L'audit calculé, None si sa création a échoué.

        Raises:
            zipfile.BadZipFile: Si une archive .zip est invalide.
            ValueError: Archive trop volumineuse, fichier non UTF-8, aucun fichier
                exploitable ou enregistrement d'un fichier impossible.
        """
        fichiers: list[Fichier] = []

        # Le dossier temporaire ne sert qu'à l'extraction, il est supprimé à la sortie du with
        with tempfile.TemporaryDirectory(prefix="audit_") as tmp:
            dossier_temp = Path(tmp)
            for upload in liste_fichier:
                nom = Path(upload.filename).name  # .name évite les chemins du type "../x"
                if nom.lower().endswith(".zip"):
                    self._extraire_zip(upload.file, dossier_temp)
                else:
                    with open(dossier_temp / nom, "wb") as sortie:
                        shutil.copyfileobj(upload.file, sortie)

            chemins = sorted(
                p
                for p in dossier_temp.rglob("*")
                if p.is_file() and p.suffix in EXTENSIONS_AUTORISEES
            )
            for chemin in chemins:
                try:
                    code = chemin.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    raise ValueError(
                        f"{chemin.name} n'est pas encodé en UTF-8"
                    ) from UnicodeDecodeError
                fichiers.append(Fichier(code=code, extension=chemin.suffix))

        if not fichiers:
            raise ValueError("Aucun fichier exploitable (.py, .txt, .toml)")

        for fichier in fichiers:
            if not self.dossier_service.create_fichier(fichier):  # renseigne fichier.id
                raise ValueError("Impossible d'enregistrer un fichier")

        dossier = Dossier(
            nom="",
            signature_HMAC="",
            liste_fichiers=fichiers,
            date_soumission=datetime.today(),
        )
        return dossier

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

    @log
    def analyse_CO2_audit(self, nb_entree: int) -> Audit:
        """Analyse approfondie de l'audit pour le CO2 et la complexité

        Args:
            nb_entree (int): Taille de l'entrée à utiliser pour calculer les émissions
        Returns:
            Audit: L'audit analysé en profondeur
        Raises:
            ValueError: Échec dans l'analyse de l'audit
        """
        compteur_fichier_analyse = 0
        if self.current_audit is None:
            raise ValueError("Il n'y a pas d'audit en mémoire")
        for fichier in self.current_audit.dossier.liste_fichiers:
            if fichier.extension == ".py":
                compteur_fichier_analyse += 1
                self.analyse_fichier.estimer_emission_fichier(fichier, taille_reference=nb_entree)
        if compteur_fichier_analyse == 0:
            raise ValueError("Pas de fichier possible à analyser")
        try:
            self.current_audit.lancer(CO2=True)
        except ValueError:
            raise ValueError("Échec dans l'analyse de l'audit") from ValueError
        return self.current_audit

    @log
    def generer_sbom(self, id_audit: int) -> dict | None:
        """Génère le SBOM (CycloneDX) d'un audit enregistré .

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            dict | None: Le SBOM sous forme de dictionnaire JSON, None si l'audit n'existe pas.
        """
        audit = self.find_audit(id_audit)
        if audit is None:
            return None
        return json.loads(SBOM().generer_sbom(audit))

    @log
    def generer_certificat(self, id_audit: int) -> Certificat | None:
        """Applique la Quality Gate à un audit enregistré et produit son certificat .
        La fonction calcule aussi la signature propre au certificat

        Args:
            id_audit (int): Identifiant de l'audit.

        Returns:
            Certificat | None: Le certificat (validé ou non), None si l'audit n'existe pas.
        """
        audit = self.find_audit(id_audit)
        if audit is None:
            return None
        certificat = Certificat(audit=audit, date_delivrance=datetime.now())
        certificat.calcul_QualityGate()
        certificat.calcul_cle()
        return certificat

    @log
    def verif_certificat(self, certificat) -> Audit | None:
        """Méthode permettant de décrypter des données cryptées et de vérifier si ces dernières correspondent au format de l'application

        Args
        ----
            cle_certificat (str) : Données cryptées à analyser
        Returns
        -------
            Audit | None : Renvoie l'audit correspondant aux données cryptées, None si le format est incorrect
        """
        cle_certificat = certificat.signature
        message = f"{certificat.id_audit}|{certificat.date_delivrance}"
        decrypt = decrypt_certificat(message, cle_certificat)
        if decrypt:
            return self.audit_dao.find_audit(certificat.id_audit)
        else:
            return None
