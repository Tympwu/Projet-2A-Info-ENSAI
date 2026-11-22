from datetime import datetime

from business_object.audit import Audit
from utils.security import crypter_certificat


class Certificat:
    """
    Certificat d'attestation délivré (ou refusé) à la suite d'un audit (F5).

    La Quality Gate décide si le certificat est validé. Chaque critère non respecté
    est expliqué dans `motifs`, pour que l'utilisateur sache quoi corriger.

    Attributs
    ---------
    SEUIL_SCORE (float): Note sur 20 que l'audit doit dépasser strictement pour être certifié.
    id (int | None): Identifiant de l'audit certifié.
    nom (str): Nom du projet audité.
    date_delivrance (datetime | None): Date de délivrance du certificat.
    statut (str): "en attente", "validé", "échoué" ou "rejeté".
    motifs (list[str]): Raisons du refus (vide si le certificat est validé).
    audit (Audit | None): Audit certifié.
    """

    SEUIL_SCORE: float = 15.0

    def __init__(
        self,
        audit: Audit | None,
        date_delivrance: datetime | None = None,
    ) -> None:
        self.audit = audit

        self.id = None if audit is None else audit.id
        if audit is not None:
            self.nom = audit.dossier.nom or f"Audit n°{audit.id}"
        else:
            self.nom = ""
        self.date_delivrance = date_delivrance
        self.statut = "en attente"
        self.motifs: list[str] = []
        self.cle: bytes = None

    def calcul_QualityGate(self, seuil_co2: float | None = None) -> bool:
        """
        Vérifie si l'audit remplit les critères de qualité (Quality Gate).

        Critères :
        - l'audit doit être terminé (sinon le certificat est "rejeté") ;
        - la note de l'audit (sur 20) doit être strictement supérieure à `SEUIL_SCORE` ;
        - si `seuil_co2` est donné et que les émissions sont connues, elles ne doivent
          pas dépasser `seuil_co2` (en gCO2e).

        Args:
            seuil_co2 (float | None): Émissions maximales autorisées en gCO2e.
                None = pas de critère carbone.

        Returns:
            bool: True si le certificat est validé, False sinon.
        """
        self.motifs = []

        # 1. Un audit absent ou pas terminé ne peut pas être certifié.
        if self.audit is None or not self.audit.statut or self.audit.statut in ("créé", "échoué"):
            self.statut = "rejeté"

            self.motifs.append("L'audit n'a pas été mené à son terme.")
            return False

        # 2. Note globale (sécurité + sobriété)
        if self.audit.score is None:
            self.motifs.append("La note de l'audit n'a pas été calculée.")
        elif self.audit.score <= self.SEUIL_SCORE:
            self.motifs.append(
                f"Note insuffisante : {self.audit.score:.1f}/20 "
                f"(il faut plus de {self.SEUIL_SCORE:.0f}/20)."
            )

        # 3. Critère carbone
        emission = self.audit.emissionCO2_total
        if seuil_co2 is not None and emission is not None and emission > seuil_co2:
            self.motifs.append(
                f"Empreinte carbone trop élevée : {emission:.3g} gCO2e (seuil : {seuil_co2:.3g})."
            )

        self.statut = "validé" if not self.motifs else "échoué"
        return self.statut == "validé"

    def calcul_cle(self):
        """Calcul la clé crypté correspondant à l'audit et la stocke dans *self.cle*"""
        data = f"{self.audit.id}|{self.date_delivrance}"
        self.cle = crypter_certificat(data)