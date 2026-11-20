"""
Tests unitaires de la classe Audit.

Lancer :
pytest tests/test_business_object/test_audit.py -v
"""

from datetime import datetime
from types import SimpleNamespace

import pytest

from business_object.audit import Audit

# ---------- Fonctions utilitaires ----------


def creer_fichier(
    id=0,
    score=None,
    emission=None,
    complexite=None,
    extension=".py",
):
    """
    Faux fichier contenant les attributs utilisés par Audit.

    complexite : exposant k de O(n^k), ou None si inconnu.
    extension : ".py" par défaut.
    """
    return SimpleNamespace(
        id=id,
        score=score,
        emissionCO2=emission,
        complexite=complexite,
        extension=extension,
    )


def creer_audit(*fichiers, **options) -> Audit:
    """
    Crée un audit avec un faux dossier.

    Le dossier fournit uniquement obtenir_fichiers(),
    qui est la méthode utilisée par Audit.
    """
    dossier = SimpleNamespace(obtenir_fichiers=lambda: list(fichiers))
    return Audit(id=1, dossier=dossier, **options)


# ---------- Création ----------


def test_valeurs_par_defaut():
    audit = creer_audit()

    assert audit.statut == "créé"
    assert audit.score is None
    assert audit.emissionCO2_total is None
    assert isinstance(audit.date, datetime)


# ---------- Score ----------


def test_calculer_score_est_le_max_et_se_stocke():
    """Une seule faille critique suffit : le score de l'audit est le pire score."""
    audit = creer_audit(
        creer_fichier(0, score=2),
        creer_fichier(1, score=9.8),
    )

    assert audit.calculer_score() == 9.8
    assert audit.score == 9.8


def test_calculer_score_dossier_vide():
    with pytest.raises(ValueError):
        creer_audit().calculer_score()


def test_calculer_score_refuse_un_score_manquant():
    audit = creer_audit(
        creer_fichier(0, score=2),
        creer_fichier(1, score=None),
    )

    with pytest.raises(ValueError):
        audit.calculer_score()


# ---------- Complexité ----------


def test_obtenir_complexites_ignore_les_valeurs_absentes():
    audit = creer_audit(
        creer_fichier(0, complexite=1),
        creer_fichier(1, complexite=2),
        creer_fichier(2, complexite=None),
    )

    assert audit.obtenir_complexites() == {0: 1, 1: 2}


def test_obtenir_complexites_garde_zero():
    """k = 0 correspond à O(1), une valeur valide."""
    audit = creer_audit(
        creer_fichier(0, complexite=0),
        creer_fichier(1, complexite=None),
    )

    assert audit.obtenir_complexites() == {0: 0}


@pytest.mark.parametrize(
    "ks",
    [(1, 2), (2, 1)],
    ids=["pire en dernier", "pire en premier"],
)
def test_calculer_complexite_retourne_le_plus_grand_k(ks):
    audit = creer_audit(*[creer_fichier(i, complexite=k) for i, k in enumerate(ks)])

    assert audit.calculer_complexite() == max(ks)


def test_calculer_complexite_ignore_les_inconnus():
    audit = creer_audit(
        creer_fichier(0, complexite=None),
        creer_fichier(1, complexite=1),
    )

    assert audit.calculer_complexite() == 1


def test_calculer_complexite_zero_est_une_valeur_valide():
    audit = creer_audit(creer_fichier(0, complexite=0))

    assert audit.calculer_complexite() == 0


def test_calculer_complexite_none_sans_complexite_exploitable():
    audit = creer_audit(
        creer_fichier(0, complexite=None),
        creer_fichier(1, complexite=None),
    )

    assert audit.calculer_complexite() is None


def test_calculer_complexite_dossier_vide():
    assert creer_audit().calculer_complexite() is None


# ---------- Lancement de l'audit ----------


@pytest.mark.parametrize(
    "score, statut",
    [
        (0, "validé"),
        (4.9, "validé"),
        (5, "refusé"),
        (9, "refusé"),
    ],
    ids=["0", "4.9", "5 (seuil : refusé)", "9"],
)
def test_lancer_statut_selon_le_score(score, statut):
    audit = creer_audit(creer_fichier(0, score=score, emission=0.1))

    assert audit.lancer() is True
    assert audit.statut == statut
    assert audit.score == score


def test_lancer_additionne_les_emissions():
    """Vérifie le calcul des émissions lorsque CO2=True."""
    audit = creer_audit(
        creer_fichier(0, score=1, emission=0.1),
        creer_fichier(1, score=1, emission=0.2),
    )

    assert audit.lancer(CO2=True) is True
    assert audit.emissionCO2_total == pytest.approx(0.3)


def test_lancer_sans_calcul_co2():
    """Un audit peut être lancé sans calculer les émissions."""
    audit = creer_audit(creer_fichier(0, score=2, emission=None))

    assert audit.lancer() is True
    assert audit.score == 2
    assert audit.statut == "validé"
    assert audit.emissionCO2_total is None


@pytest.mark.parametrize(
    "fichiers, calcul_co2",
    [
        pytest.param(
            [],
            False,
            id="dossier vide",
        ),
        pytest.param(
            [creer_fichier(0, score=None, emission=0.1)],
            False,
            id="score manquant",
        ),
        pytest.param(
            [creer_fichier(0, score=1, emission=None)],
            True,
            id="emission manquante",
        ),
    ],
)
def test_lancer_echoue_si_une_donnee_manque(fichiers, calcul_co2):
    audit = creer_audit(*fichiers)

    with pytest.raises(ValueError):
        audit.lancer(CO2=calcul_co2)

    assert audit.statut == "échoué"
    assert audit.emissionCO2_total is None


# ---------- Affichage ----------


def test_repr():
    audit = creer_audit(date=datetime(2026, 11, 3))

    assert repr(audit) == (
        "Audit(id=1, date=03/11/2026, statut=créé, score=None, emissionCO2_total=None)"
    )
