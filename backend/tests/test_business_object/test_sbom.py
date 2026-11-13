"""Tests unitaires pour le business object SBOM."""

import json
from unittest.mock import MagicMock
import pytest
from business_object.sbom import SBOM
from business_object.audit import Audit


def test_sbom_init_defaut():
    """Vérifie l'initialisation du SBOM avec le format par défaut."""
    sbom_gen = SBOM()
    assert sbom_gen.format == "CycloneDX"


def test_sbom_init_personnalise():
    """Vérifie l'initialisation du SBOM avec un format personnalisé."""
    sbom_gen = SBOM(format="SPDX")
    assert sbom_gen.format == "SPDX"


def test_generer_sbom():
    """Vérifie la génération correcte du SBOM au format JSON à partir d'un audit."""
    # Création d'une dépendance mockée
    dep = MagicMock()
    dep.nom = "requests"
    dep.version = "2.28.0"
    dep.auteur = "Kenneth Reitz"

    # Simulation de la structure : audit -> dossier -> obtenir_dependances_dossier()
    audit_mock = MagicMock(spec=Audit)
    audit_mock.dossier.obtenir_dependances_dossier.return_value = [dep]

    sbom_gen = SBOM(format="CycloneDX")
    resultat_json = sbom_gen.generer_sbom(audit_mock)

    # Conversion du JSON généré en dictionnaire pour validation facile
    data = json.loads(resultat_json)

    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.6"
    assert data["version"] == 1
    assert len(data["components"]) == 1
    
    composant = data["components"][0]
    assert composant["type"] == "library"
    assert composant["name"] == "requests"
    assert composant["version"] == "2.28.0"
    assert composant["author"] == "Kenneth Reitz"