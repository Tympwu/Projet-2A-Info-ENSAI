"""Tests unitaires pour le business object Certificat."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from business_object.certificat import Certificat


@pytest.fixture
def faux_audit():
    """Crée un faux audit terminé, avec un score sous le seuil."""
    audit = MagicMock()  # pas de spec=Audit : `dossier` est un attribut d'instance
    audit.id = 1
    audit.dossier.nom = "ProjetTest"
    audit.statut = "validé"
    audit.score = 4.0
    audit.emissionCO2_total = None
    return audit


def test_certificat_init(faux_audit):
    """Vérifie l'initialisation correcte du certificat à partir d'un audit."""
    date_fixe = datetime(2026, 1, 1, 10, 0)
    cert = Certificat(audit=faux_audit, date_delivrance=date_fixe)

    assert cert.id == 1
    assert cert.nom == "ProjetTest"
    assert cert.date_delivrance == date_fixe
    assert cert.statut == "en attente"
    assert cert.motifs == []
    assert cert.audit == faux_audit


def test_certificat_nom_par_defaut(faux_audit):
    """Sans nom de dossier, le certificat prend le numéro de l'audit."""
    faux_audit.dossier.nom = ""
    assert Certificat(audit=faux_audit).nom == "Audit n°1"


def test_calcul_quality_gate_rejete_audit_none():
    """Le certificat est rejeté si l'audit est None."""
    cert = Certificat(audit=None)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "rejeté"


@pytest.mark.parametrize("statut", [None, "", "créé", "échoué"])
def test_calcul_quality_gate_rejete_audit_non_termine(faux_audit, statut):
    """Le certificat est rejeté si l'audit n'est pas terminé."""
    faux_audit.statut = statut
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "rejeté"


def test_calcul_quality_gate_valide(faux_audit):
    """Le certificat est validé si le score est inférieur au seuil."""
    faux_audit.score = 3.5
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is True
    assert cert.statut == "validé"
    assert cert.motifs == []


def test_calcul_quality_gate_echoue_score(faux_audit):
    """Le certificat échoue si le score atteint le seuil, avec un motif explicite."""
    faux_audit.score = 7.5
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "échoué"
    assert "vulnérabilité" in cert.motifs[0]


def test_calcul_quality_gate_echoue_score_absent(faux_audit):
    """Un score non calculé ne peut pas être validé."""
    faux_audit.score = None
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "échoué"


def test_calcul_quality_gate_echoue_carbone(faux_audit):
    """Le certificat échoue si les émissions dépassent le seuil carbone."""
    faux_audit.emissionCO2_total = 2.0
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate(seuil_co2=1.0) is False
    assert "carbone" in cert.motifs[0]


def test_calcul_quality_gate_carbone_ignore_sans_seuil(faux_audit):
    """Sans seuil carbone, les émissions ne bloquent pas le certificat."""
    faux_audit.emissionCO2_total = 1000.0
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is True


def test_calcul_quality_gate_cumule_les_motifs(faux_audit):
    """Tous les critères non respectés sont listés."""
    faux_audit.score = 9.8
    faux_audit.emissionCO2_total = 2.0
    cert = Certificat(audit=faux_audit)

    cert.calcul_QualityGate(seuil_co2=1.0)

    assert len(cert.motifs) == 2