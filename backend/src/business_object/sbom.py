import json
import re
import uuid
from datetime import UTC, datetime

from business_object.audit import Audit


class SBOM:
    """
    Génère le SBOM (Software Bill of Materials) d'un audit, au format CycloneDX 1.6 .

    Le SBOM est l'inventaire des composants logiciels (dépendances) d'un projet.
    Chaque composant est identifié par un purl (Package URL), par exemple
    `pkg:pypi/requests@2.31.0`, ce qui permet à d'autres outils de le reconnaître.

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

    @staticmethod
    def normaliser_nom(nom: str) -> str:
        """Normalise un nom de paquet PyPI (PEP 503) : `Py_YAML` devient `py-yaml`."""
        return re.sub(r"[-_.]+", "-", nom).lower()

    def _composants(self, dependances: list) -> list[dict]:
        """
        Transforme les dépendances en composants CycloneDX, sans doublon.

        Si une même bibliothèque apparaît avec et sans version (par exemple `requests`
        importé dans un .py et `requests==2.31.0` dans requirements.txt), seule la
        version précise est gardée.
        """
        avec_version = {self.normaliser_nom(d.nom) for d in dependances if d.version}
        deja_vus = set()
        composants = []

        for dep in dependances:
            nom = self.normaliser_nom(dep.nom)
            if dep.version is None and nom in avec_version:
                continue
            if (nom, dep.version) in deja_vus:
                continue
            deja_vus.add((nom, dep.version))

            purl = f"pkg:pypi/{nom}@{dep.version}" if dep.version else f"pkg:pypi/{nom}"
            composant = {"type": "library", "bom-ref": purl, "name": dep.nom, "purl": purl}
            if dep.version:
                composant["version"] = dep.version
            if dep.auteur:
                composant["author"] = dep.auteur
            composants.append(composant)

        return sorted(composants, key=lambda c: c["bom-ref"])

    def generer_sbom(self, audit: Audit) -> str:
        """
        Génère le SBOM des dépendances du dossier audité.

        Parameters
        ----------
        audit (Audit): Audit dont on veut l'inventaire des dépendances.

        Returns
        -------
        str: SBOM au format JSON CycloneDX.
        """
        nom_projet = audit.dossier.nom or f"audit-{audit.id}"
        sbom = {
            "bomFormat": self.format,
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "tools": {"components": [{"type": "application", "name": "CleanOps"}]},
                "component": {
                    "type": "application",
                    "bom-ref": f"audit-{audit.id}",
                    "name": nom_projet,
                },
            },
            "components": self._composants(audit.dossier.obtenir_dependances_dossier()),
        }
        return json.dumps(sbom, indent=2, ensure_ascii=False)
