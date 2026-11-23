"""Tests des exports SBOM et certificat : service et routes."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from business_object.audit import Audit
from business_object.certificat import Certificat
from business_object.dossier import Dossier
from business_object.fichier import Fichier
from controller import audit_controller
from service.audit_service import AuditService


def un_audit(score=18.0, statut="validé") -> Audit:
    """Audit enregistré avec un requirements.txt contenant une dépendance épinglée."""
    fichier = Fichier(code="requests==2.31.0\n", extension=".txt", id=1)
    dossier = Dossier(nom="", liste_fichiers=[fichier])
    return Audit(dossier=dossier, id=3, score=score, statut=statut)


@pytest.fixture
def service():
    """AuditService dont le DAO est remplacé par un faux (pas de base de données)."""
    service = AuditService()
    service.audit_dao = MagicMock()  # AuditService est un singleton : on remplace son DAO
    return service


# --- Service ---


def test_generer_sbom_audit_existant(service):
    service.audit_dao.find_audit.return_value = un_audit()

    sbom = service.generer_sbom(3)

    assert sbom["components"][0]["purl"] == "pkg:pypi/requests@2.31.0"
    service.audit_dao.find_audit.assert_called_once_with(3)


def test_generer_sbom_audit_inexistant(service):
    service.audit_dao.find_audit.return_value = None

    assert service.generer_sbom(99) is None


def test_generer_certificat_valide(service):
    service.audit_dao.find_audit.return_value = un_audit(score=18.0)

    certificat = service.generer_certificat(3)

    assert certificat.statut == "validé"
    assert certificat.date_delivrance is not None
    assert certificat.cle  # le certificat porte sa signature


def test_certificat_signe_verifiable(service):
    """Un certificat délivré est reconnu comme authentique par verif_certificat."""
    audit = un_audit(score=18.0)
    service.audit_dao.find_audit.return_value = audit
    certificat = service.generer_certificat(3)

    demande = SimpleNamespace(
        id_audit=3, date_delivrance=certificat.date_delivrance, signature=certificat.cle
    )

    assert service.verif_certificat(demande) is audit


def test_certificat_falsifie_refuse(service):
    """Modifier l'audit ou la date d'un certificat invalide sa signature."""
    service.audit_dao.find_audit.return_value = un_audit(score=18.0)
    certificat = service.generer_certificat(3)

    autre_audit = SimpleNamespace(
        id_audit=4, date_delivrance=certificat.date_delivrance, signature=certificat.cle
    )
    signature_inventee = SimpleNamespace(
        id_audit=3, date_delivrance=certificat.date_delivrance, signature="AAAA"
    )

    assert service.verif_certificat(autre_audit) is None
    assert service.verif_certificat(signature_inventee) is None


def test_generer_certificat_refuse(service):
    service.audit_dao.find_audit.return_value = un_audit(score=9.8, statut="refusé")

    certificat = service.generer_certificat(3)

    assert certificat.statut == "échoué"
    assert certificat.motifs


def test_generer_certificat_audit_inexistant(service):
    service.audit_dao.find_audit.return_value = None

    assert service.generer_certificat(99) is None


# --- Routes (sans lancer toute l'API ni la base de données) ---


@pytest.fixture
def client():
    """Petite application qui ne contient que les routes d'audit, avec un service simulé."""
    faux_service = MagicMock()
    app = FastAPI()
    app.include_router(audit_controller.router, prefix="/audit")
    app.dependency_overrides[audit_controller.get_audit_service] = lambda: faux_service
    return TestClient(app), faux_service


def test_route_sbom(client):
    client, faux_service = client
    faux_service.generer_sbom.return_value = {"bomFormat": "CycloneDX", "components": []}

    reponse = client.get("/audit/3/sbom")

    assert reponse.status_code == 200
    assert reponse.json()["bomFormat"] == "CycloneDX"
    assert "sbom_audit_3.json" in reponse.headers["content-disposition"]


def test_route_sbom_404(client):
    client, faux_service = client
    faux_service.generer_sbom.return_value = None

    assert client.get("/audit/99/sbom").status_code == 404


def test_route_certificat(client):
    client, faux_service = client
    audit = un_audit(score=9.8, statut="refusé")
    certificat = Certificat(audit=audit)
    certificat.calcul_QualityGate()
    faux_service.generer_certificat.return_value = certificat

    reponse = client.get("/audit/3/certificat")

    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["audit_id"] == 3
    assert donnees["statut"] == "échoué"
    assert donnees["score"] == 9.8
    assert donnees["motifs"]


def test_route_certificat_404(client):
    client, faux_service = client
    faux_service.generer_certificat.return_value = None

    assert client.get("/audit/99/certificat").status_code == 404


def test_route_verif_certificat_authentique(client):
    client, faux_service = client
    faux_service.verif_certificat.return_value = un_audit(score=18.0)
    demande = {"signature": "abc", "id_audit": 3, "date_delivrance": "2026-11-23T20:00:00"}

    reponse = client.post("/audit/verif_certificat", json=demande)

    assert reponse.status_code == 200
    assert reponse.json()["id"] == 3


def test_route_verif_certificat_invalide(client):
    client, faux_service = client
    faux_service.verif_certificat.return_value = None
    demande = {"signature": "faux", "id_audit": 3, "date_delivrance": "2026-11-23T20:00:00"}

    assert client.post("/audit/verif_certificat", json=demande).status_code == 404
