"""
Tests de la classe Audit.

Lancer : pytest tests/test_business_object/test_audit.py -v

"""
from datetime import datetime
from types import SimpleNamespace

import pytest

from business_object.audit import Audit
from business_object.fichier import Fichier


def creer_fichier(id=0, score=None, emission=None, complexite=None) -> Fichier:
    """Fichier en mémoire : Audit n'a pas besoin qu'il existe sur le disque."""
    return Fichier(
        chemin=f"f{id}.py", id=id, score=score, emissionCO2=emission, complexite=complexite
    )


def creer_audit(*fichiers, **options) -> Audit:
    """Audit dont le dossier ne fournit que obtenir_fichiers(), seule méthode utilisée par Audit."""
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

# sera à modifier après le calcul du CO2
def test_calculer_score_est_la_moyenne_et_se_stocke():
    audit = creer_audit(creer_fichier(0, score=2), creer_fichier(1, score=4))
    assert audit.calculer_score() == 3.0
    assert audit.score == 3.0


def test_calculer_score_dossier_vide():
    with pytest.raises(ValueError):
        creer_audit().calculer_score()


def test_calculer_score_refuse_un_score_manquant():
    audit = creer_audit(creer_fichier(0, score=2), creer_fichier(1, score=None))
    with pytest.raises(ValueError):
        audit.calculer_score()


# ---------- Complexité ----------

def test_obtenir_complexites_ignore_les_valeurs_inconnues():
    audit = creer_audit(
        creer_fichier(0, complexite="O(n)"),
        creer_fichier(1, complexite="O(n²)"),
        creer_fichier(2, complexite=None),
        creer_fichier(3, complexite="inconnue"),
    )
    assert audit.obtenir_complexites() == {0: "O(n)", 1: "O(n²)"}


@pytest.mark.parametrize("complexites", [("O(n)", "O(n²)"), ("O(n²)", "O(n)")])
def test_calculer_complexite_retourne_le_rang_de_la_pire(complexites):
    """Le rang est la position dans l'échelle + 1, quel que soit l'ordre des fichiers."""
    audit = creer_audit(*[creer_fichier(i, complexite=c) for i, c in enumerate(complexites)])
    assert audit.calculer_complexite() == Fichier.ECHELLE_COMPLEXITE.index("O(n²)") + 1


def test_calculer_complexite_donne_zero_sans_complexite_exploitable():
    audit = creer_audit(creer_fichier(0, complexite=None), creer_fichier(1, complexite="inconnue"))
    assert audit.calculer_complexite() == 0


# ---------- lancer() ----------

@pytest.mark.parametrize(
    "score, statut",
    [(0, "validé"), (4.9, "validé"), (5, "refusé"), (9, "refusé")],
    ids=["0", "4.9", "5 (seuil : refusé)", "9"],
)
def test_lancer_statut_selon_le_score(score, statut):
    audit = creer_audit(creer_fichier(0, score=score, emission=0.1))
    assert audit.lancer() is True
    assert audit.statut == statut
    assert audit.score == score


def test_lancer_additionne_les_emissions():
    audit = creer_audit(
        creer_fichier(0, score=1, emission=0.1), creer_fichier(1, score=1, emission=0.2)
    )
    audit.lancer()
    assert audit.emissionCO2_total == pytest.approx(0.3)


@pytest.mark.parametrize(
    "fichiers",
    [
        pytest.param([], id="dossier vide"),
        pytest.param([creer_fichier(0, score=None, emission=0.1)], id="score manquant"),
        pytest.param([creer_fichier(0, score=1, emission=None)], id="émission manquante"),
    ],
)
def test_lancer_echoue_si_une_donnee_manque(fichiers):
    audit = creer_audit(*fichiers)
    with pytest.raises(ValueError):
        audit.lancer()
    assert audit.statut == "échoué"
    assert audit.emissionCO2_total is None


# ---------- Affichage ----------

def test_repr():
    audit = creer_audit(date=datetime(2026, 11, 3))
    assert repr(audit) == (
        "Audit(id=1, date=03/11/2026, statut=créé, score=None, emissionCO2_total=None)"
    )
