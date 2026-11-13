import json

from business_object.audit import Audit


class SBOM:
    """
    Génère le SBOM (Software Bill of Materials) d'un audit.

    Le SBOM est l'inventaire des composants logiciels (dépendances) d'un projet.

    Attributes
    ---------
    format (str): Format du SBOM (par défaut "CycloneDX").
    """

    def __init__(self, format: str = "CycloneDX") -> None:
        """
        Initialise un générateur de SBOM.

        Parameters
        ----------
        format (str): Format du SBOM (par défaut "CycloneDX").

        """
        self.format: str = format

    def generer_sbom(self, audit: Audit) -> str:
        """
        Génère le SBOM des dépendances du dossier audité.

        Parameters
        ----------
        audit (Audit): Audit dont on veut l'inventaire des dépendances.

        Returns
        -------
        str: SBOM au format JSON (nom, version et auteur de chaque composant).
        """
        composants = [
            {"type": "library", "name": d.nom, "version": d.version, "author": d.auteur}
            for d in audit.dossier.obtenir_dependances_dossier()
        ]
        sbom = {
            "bomFormat": self.format,
            "specVersion": "1.6",
            "version": 1,
            "components": composants,
        }
        return json.dumps(sbom, indent=2, ensure_ascii=False)
