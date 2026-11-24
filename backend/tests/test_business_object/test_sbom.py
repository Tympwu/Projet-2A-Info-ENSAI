"""Tests unitaires pour le business object SBOM."""

import json
from unittest.mock import MagicMock

from business_object.dependance import Dependances
from business_object.sbom import SBOM


def faux_audit(dependances):
    """Crée un faux audit dont le dossier contient les dépendances données."""
    audit = MagicMock()
    audit.id = 7
    audit.dossier.nom = "ProjetTest"
    audit.dossier.obtenir_dependances_dossier.return_value = dependances
    return audit


def test_sbom_init_defaut():
    """Vérifie l'initialisation du SBOM avec le format par défaut."""
    assert SBOM().format == "CycloneDX"


def test_sbom_init_personnalise():
    """Vérifie l'initialisation du SBOM avec un format personnalisé."""
    assert SBOM(format="SPDX").format == "SPDX"


def test_normaliser_nom():
    """Les noms PyPI sont normalisés selon la PEP 503."""
    assert SBOM.normaliser_nom("Py_YAML") == "py-yaml"
    assert SBOM.normaliser_nom("zope.interface") == "zope-interface"


def test_generer_sbom_structure_cyclonedx():
    """Le SBOM contient les champs obligatoires de CycloneDX 1.6."""
    deps = [Dependances(nom="requests", version="2.31.0", auteur="Kenneth Reitz")]

    data = json.loads(SBOM().generer_sbom(faux_audit(deps)))

    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.6"
    assert data["version"] == 1
    assert data["serialNumber"].startswith("urn:uuid:")
    assert data["metadata"]["component"]["name"] == "ProjetTest"
    composant = data["components"][0]
    assert composant["type"] == "library"
    assert composant["name"] == "requests"
    assert composant["version"] == "2.31.0"
    assert composant["purl"] == "pkg:pypi/requests@2.31.0"
    assert composant["bom-ref"] == composant["purl"]
    assert composant["author"] == "Kenneth Reitz"


def test_generer_sbom_garde_la_version_precise():
    """Un import sans version est ignoré si la même bibliothèque a une version précise."""
    deps = [
        Dependances(nom="requests", version=None, auteur=None),
        Dependances(nom="requests", version="2.31.0", auteur=None),
        Dependances(nom="numpy", version=None, auteur=None),
    ]

    data = json.loads(SBOM().generer_sbom(faux_audit(deps)))

    purls = [c["purl"] for c in data["components"]]
    assert purls == ["pkg:pypi/numpy", "pkg:pypi/requests@2.31.0"]
    assert "version" not in data["components"][0]
    assert "author" not in data["components"][0]


def test_generer_sbom_sans_dependance():
    """Un dossier sans dépendance donne un SBOM valide mais vide."""
    data = json.loads(SBOM().generer_sbom(faux_audit([])))

    assert data["components"] == []
