"""Tests unitaires pour le business object Dependances."""

from unittest.mock import patch
import pytest
from business_object.dependance import Dependances


def test_dependances_init():
    """Vérifie l'initialisation des attributs de la dépendance."""
    dep = Dependances(nom="requests", version="2.28.0", auteur="Kenneth Reitz")
    
    assert dep.nom == "requests"
    assert dep.version == "2.28.0"
    assert dep.auteur == "Kenneth Reitz"


@patch("business_object.dependance.Vulnerabilite")
def test_a_vulnerabilite_succes(mock_vulnerabilite_class):
    """Vérifie la création correcte des vulnérabilités au-dessus du seuil."""
    dep = Dependances(nom="requests", version="2.28.0", auteur=None)
    
    data_api = {
        "vulns": [
            {"id": "CVE-2023-0001", "summary": "Bug critique"},
            {"id": "CVE-2023-0002", "details": "Autre bug important"}
        ]
    }
    scores = [8.5, 7.0]  # Tous les deux >= seuil par défaut (7.0)

    dep.a_vulnerabilite(data_api, scores)

    assert mock_vulnerabilite_class.call_count == 2
    mock_vulnerabilite_class.assert_any_call(
        description="CVE-2023-0001 : Bug critique",
        score_danger=8.5
    )
    mock_vulnerabilite_class.assert_any_call(
        description="CVE-2023-0002 : Autre bug important",
        score_danger=7.0
    )


@patch("business_object.dependance.Vulnerabilite")
def test_a_vulnerabilite_filtrage(mock_vulnerabilite_class):
    """Vérifie que les scores inférieurs au seuil ou None sont ignorés."""
    dep = Dependances(nom="requests", version="2.28.0", auteur=None)
    
    data_api = {
        "vulns": [
            {"id": "CVE-LOW", "summary": "Faible"},
            {"id": "CVE-NONE", "summary": "Inconnu"},
            {"id": "CVE-HIGH", "summary": "Haut"}
        ]
    }
    scores = [5.0, None, 9.0]  # 5.0 < 7.0, None, et 9.0 >= 7.0

    dep.a_vulnerabilite(data_api, scores, seuil=7.0)

    # Seul CVE-HIGH doit être retenu
    mock_vulnerabilite_class.assert_called_once_with(
        description="CVE-HIGH : Haut",
        score_danger=9.0
    )


def test_a_vulnerabilite_value_error():
    """Vérifie qu'une exception ValueError est levée si les longueurs diffèrent."""
    dep = Dependances(nom="requests", version="2.28.0", auteur=None)
    data_api = {"vulns": [{"id": "CVE-1"}]}
    scores = [8.0, 9.0]  # 1 fiche pour 2 scores

    with pytest.raises(ValueError, match="Chaque fiche OSV doit avoir un score associé."):
        dep.a_vulnerabilite(data_api, scores)
