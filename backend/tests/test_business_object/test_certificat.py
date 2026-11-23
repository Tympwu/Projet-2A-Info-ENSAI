"""Tests unitaires pour le business object Certificat."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from business_object.certificat import Certificat


@pytest.fixture
def faux_audit():
    """Crée un faux audit terminé, avec une note au-dessus du seuil (sur 20)."""
    audit = MagicMock()  # pas de spec=Audit : `dossier` est un attribut d'instance
    audit.id = 1
    audit.dossier.nom = "ProjetTest"
    audit.statut = "validé"
    audit.score = 18.0
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
    """Le certificat est validé si la note dépasse strictement le seuil de 15/20."""
    faux_audit.score = 16.5
    cert = Certificat(audit=faux_audit)


    assert cert.calcul_QualityGate() is True
    assert cert.statut == "validé"
    assert cert.motifs == []


def test_calcul_quality_gate_echoue_score(faux_audit):
    """Le certificat échoue si la note ne dépasse pas le seuil, avec un motif explicite."""
    faux_audit.score = 12.0
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "échoué"
    assert "Note insuffisante" in cert.motifs[0]


def test_calcul_quality_gate_seuil_exact_refuse(faux_audit):
    """Une note de exactement 15/20 ne suffit pas : il faut la dépasser."""
    faux_audit.score = 15.0
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False


def test_calcul_quality_gate_echoue_score_absent(faux_audit):
    """Un score non calculé ne peut pas être validé."""
    faux_audit.score = None
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is False
    assert cert.statut == "échoué"



def test_calcul_quality_gate_ne_regarde_que_la_note(faux_audit):
    """Les émissions comptent déjà dans la note sur 20 : la Quality Gate ne les revérifie pas."""
    faux_audit.emissionCO2_total = 1000.0
    cert = Certificat(audit=faux_audit)

    assert cert.calcul_QualityGate() is True
