"""Tests unitaires de HistoriqueService."""

from unittest.mock import MagicMock, patch

import pytest

from business_object.audit import Audit
from business_object.historique import Historique
from service.historique_service import HistoriqueService


def un_audit(id_audit: int) -> Audit:
    """Audit minimal : depuis le passage à `code`, un Audit a toujours un dossier."""
    return Audit(id=id_audit, dossier=MagicMock())


@pytest.fixture
def faux_audit_dao():
    """Remplace AuditDao pour isoler les tests de la couche service."""
    with patch("service.historique_service.AuditDao") as faux:
        yield faux.return_value


@pytest.fixture
def service(faux_audit_dao):
    """Retourne une instance de HistoriqueService avec un DAO d'audit mocké."""
    return HistoriqueService()


# --- Tests de la méthode utilitaire `verifier_id` ---


@pytest.mark.parametrize("valeur_invalide", [0, -1, "1", None, 1.5])
def test_verifier_id_invalide(valeur_invalide):
    """Vérifie qu'une exception ValueError est levée si l'ID n'est pas un entier strictement positif."""
    with pytest.raises(ValueError):
        HistoriqueService.verifier_id(valeur_invalide, "id_test")


def test_verifier_id_valide():
    """Vérifie qu'aucune exception n'est levée pour un entier valide."""
    try:
        HistoriqueService.verifier_id(5, "id_test")
    except ValueError:
        pytest.fail("verifier_id a levé une ValueError pour un ID valide.")


# --- Tests de la méthode `consulter_historique` ---


def test_consulter_historique_succes(service, faux_audit_dao):
    """Vérifie la construction correcte de l'objet Historique pour un utilisateur valide."""
    audits_fictifs = [un_audit(1), un_audit(2)]
    faux_audit_dao.find_by_utilisateur.return_value = audits_fictifs

    historique = service.consulter_historique(id_utilisateur=3)

    assert isinstance(historique, Historique)
    assert historique.id == 3
    assert historique.audits == audits_fictifs
    faux_audit_dao.find_by_utilisateur.assert_called_once_with(3)


def test_consulter_historique_id_invalide(service):
    """Vérifie que la consultation lève une ValueError si l'ID utilisateur est invalide."""
    with pytest.raises(ValueError):
        service.consulter_historique(id_utilisateur=0)


# --- Tests de la méthode `supprimer_audit_historique` ---


def test_supprimer_audit_historique_succes(service, faux_audit_dao):
    """Vérifie la suppression réussie d'un audit existant."""
    audit_existant = un_audit(10)
    faux_audit_dao.find_audit.return_value = audit_existant
    faux_audit_dao.remove_audit.return_value = True

    resultat = service.supprimer_audit_historique(id_audit=10)

    assert resultat is True
    faux_audit_dao.find_audit.assert_called_once_with(10)
    faux_audit_dao.remove_audit.assert_called_once_with(audit_existant)


def test_supprimer_audit_historique_introuvable(service, faux_audit_dao):
    """Vérifie que la suppression retourne False si l'audit n'existe pas."""
    faux_audit_dao.find_audit.return_value = None

    resultat = service.supprimer_audit_historique(id_audit=99)

    assert resultat is False
    faux_audit_dao.find_audit.assert_called_once_with(99)
    faux_audit_dao.remove_audit.assert_not_called()


def test_supprimer_audit_historique_id_invalide(service):
    """Vérifie qu'une exception est levée si l'ID d'audit à supprimer est invalide."""
    with pytest.raises(ValueError):
        service.supprimer_audit_historique(id_audit=-5)


# --- Tests de la méthode `supprimer_historique` (global) ---


def test_supprimer_historique_succes(service, faux_audit_dao):
    """Vérifie la suppression de tous les audits d'un utilisateur."""
    audits = [un_audit(1), un_audit(2)]
    faux_audit_dao.find_by_utilisateur.return_value = audits
    faux_audit_dao.remove_audit.return_value = True

    resultat = service.supprimer_historique(id_utilisateur=3)

    assert resultat is True
    assert faux_audit_dao.remove_audit.call_count == 2


def test_supprimer_historique_aucun_audit(service, faux_audit_dao):
    """Vérifie que la suppression retourne False si l'utilisateur n'a aucun audit."""
    faux_audit_dao.find_by_utilisateur.return_value = []

    resultat = service.supprimer_historique(id_utilisateur=3)

    assert resultat is False
    faux_audit_dao.remove_audit.assert_not_called()


def test_supprimer_historique_echec_partiel(service, faux_audit_dao):
    """Vérifie que la suppression globale retourne False si au moins une suppression échoue."""
    audits = [un_audit(1), un_audit(2)]
    faux_audit_dao.find_by_utilisateur.return_value = audits
    faux_audit_dao.remove_audit.side_effect = [True, False]

    resultat = service.supprimer_historique(id_utilisateur=3)

    assert resultat is False


# --- Tests de la méthode `find_all_historiques` ---


def test_find_all_historiques(service):
    """Vérifie la récupération de tous les historiques via le service utilisateur."""
    # On mocke le service utilisateur appelé en interne
    with patch("service.historique_service.UtilisateurService") as faux_user_service:
        utilisateur_mock = MagicMock()
        utilisateur_mock.historique = Historique(id=1, audits=[])
        faux_user_service.return_value.find_all_utilisateurs.return_value = [utilisateur_mock]

        historiques = service.find_all_historiques()

        assert len(historiques) == 1
        assert historiques[0].id == 1
        faux_user_service.return_value.find_all_utilisateurs.assert_called_once()
