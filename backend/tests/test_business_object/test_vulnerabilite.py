import pytest

from business_object.vulnerabilite import Vulnerabilite


@pytest.mark.parametrize(
    "score, attendu",
    [
        (8.9, False),  # juste sous le seuil
        (9.0, True),   # pile sur le seuil
        (10.0, True),  # score maximal
    ],
)
def test_est_critique(score, attendu):
    vulnerabilite = Vulnerabilite(description="faille", score_danger=score)
    assert vulnerabilite.est_critique() is attendu


@pytest.mark.parametrize("score", [-1, 10.5])
def test_init_score_hors_intervalle(score):
    with pytest.raises(ValueError):
        Vulnerabilite(description="faille", score_danger=score)
