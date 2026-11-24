"""Tests des routes /file (sans base de données : le service est simulé)."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from business_object.fichier import Fichier
from controller import fichier_controller


@pytest.fixture
def client():
    """Petite application qui ne contient que les routes /file, avec un service simulé."""
    faux_service = MagicMock()
    app = FastAPI()
    app.include_router(fichier_controller.router, prefix="/file")
    app.dependency_overrides[fichier_controller.get_dossier_service] = lambda: faux_service
    return TestClient(app), faux_service


def test_fichiers_d_un_utilisateur(client):
    """La route par utilisateur est bien atteinte (et pas confondue avec /file/{id_fichier})."""
    client, faux_service = client
    faux_service.find_fichier_by_user.return_value = [Fichier(code="x", extension=".py", id=7)]

    reponse = client.get("/file/utilisateur/2")

    assert reponse.status_code == 200
    assert reponse.json()[0]["id"] == 7
    faux_service.find_fichier_by_user.assert_called_once_with(2)
    faux_service.find_fichier_by_id.assert_not_called()


def test_fichier_par_id(client):
    client, faux_service = client
    faux_service.find_fichier_by_id.return_value = Fichier(code="x", extension=".py", id=3)

    reponse = client.get("/file/3")

    assert reponse.status_code == 200
    faux_service.find_fichier_by_id.assert_called_once_with(3)
