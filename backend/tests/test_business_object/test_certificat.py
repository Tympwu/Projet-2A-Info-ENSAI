"""Tests unitaires pour le business object Certificat."""

from datetime import datetime
from unittest.mock import MagicMock
import pytest

from business_object.certificat import Certificat
from business_object.audit import Audit


@pytest.fixture
def faux_audit():
    """Crée un faux audit pour les tests."""
    audit = MagicMock(spec=Audit)
    audit.id = 1
    audit.dossier.nom = "ProjetTest"
    audit.statut = True
    audit.score = 4.0  # Inférieur à 5.0 selon la logique actuelle de la méthode
    return audit


def test_certificat_init(faux_audit):
    """Vérifie l'initialisation correcte du certificat à partir d'un audit."""
    date_fixe = datetime(2026, 1, 1, 10, 0)
    cert = Certificat(audit=faux_audit, date_delivrance=date_fixe)

    assert cert.id == 1
    assert cert.nom == "ProjetTest"
    assert cert.date_delivrance == date_fixe
    assert cert.statut == "en attente"
    assert cert.audit == faux_audit


def test_calcul_quality_gate_rejete_audit_none():
    """Vérifie que le certificat est rejeté si l'audit est None."""
    cert = Certificat(audit=None)
    
    resultat = cert.calcul_QualityGate()

    assert resultat is False
    assert cert.statut == "rejeté"


def test_calcul_quality_gate_rejete_statut_faux(faux_audit):
    """Vérifie que le certificat est rejeté si le statut de l'audit est False/invalide."""
    faux_audit.statut = False
    cert = Certificat(audit=faux_audit)

    resultat = cert.calcul_QualityGate()

    assert resultat is False
    assert cert.statut == "rejeté"


def test_calcul_quality_gate_valide(faux_audit):
    """Vérifie que le certificat est validé si le score est inférieur à 5.0 (selon la règle actuelle)."""
    faux_audit.score = 3.5
    cert = Certificat(audit=faux_audit)

    resultat = cert.calcul_QualityGate()

    assert resultat is True
    assert cert.statut == "validé"


def test_calcul_quality_gate_echoue(faux_audit):
    """Vérifie que le certificat échoue si le score est supérieur ou égal à 5.0."""
    faux_audit.score = 7.5
    cert = Certificat(audit=faux_audit)

    resultat = cert.calcul_QualityGate()

    assert resultat is False
    assert cert.statut == "échoué"