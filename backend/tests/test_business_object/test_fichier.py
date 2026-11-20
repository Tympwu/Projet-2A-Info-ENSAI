
import ast

import pytest

from business_object.fichier import Fichier
from business_object.vulnerabilite import Vulnerabilite


def test_init_stocke_code_et_extension():
    fichier = Fichier(code="x = 1\n", extension=".py")

    assert fichier.code == "x = 1\n"
    assert fichier.extension == ".py"


def test_init_garde_extension_fournie():
    fichier = Fichier(code="x = 1\n", extension=".txt")

    assert fichier.extension == ".txt"


@pytest.mark.parametrize(
    "k, attendu",
    [
        (0, "O(1)"),
        (1, "O(n)"),
        (None, None),
        (2, "O(n^2)"),
    ],
)
def test_formater_complexite(k, attendu):
    assert Fichier.formater_complexite(k) == attendu


def test_est_a_risque_avant_analyse():
    fichier = Fichier(code="", extension=".py")

    with pytest.raises(ValueError):
        fichier.est_a_risque()


def test_est_a_risque_avec_une_vulnerabilite_critique():
    vulnerabilites = [
        Vulnerabilite(description="faille mineure", score_danger=3.0),
        Vulnerabilite(description="faille grave", score_danger=9.8),
    ]

    fichier = Fichier(
        code="",
        extension=".py",
        liste_vulnerabilites=vulnerabilites,
    )

    assert fichier.est_a_risque() is True


def test_est_a_risque_sans_vulnerabilite():
    fichier = Fichier(
        code="",
        extension=".py",
        liste_vulnerabilites=[],
    )

    assert fichier.est_a_risque() is False


def test_est_a_risque_sans_vulnerabilite_critique():
    vulnerabilites = [
        Vulnerabilite(description="faille mineure", score_danger=3.0),
        Vulnerabilite(description="faille élevée", score_danger=8.9),
    ]

    fichier = Fichier(
        code="",
        extension=".py",
        liste_vulnerabilites=vulnerabilites,
    )

    assert fichier.est_a_risque() is False


def test_lire_contenu_retourne_tout_le_texte():
    contenu = "x = 1\ny = 2\n"
    fichier = Fichier(code=contenu, extension=".py")

    assert fichier.lire_contenu() == contenu


def test_lire_contenu_vide():
    fichier = Fichier(code="", extension=".py")

    assert fichier.lire_contenu() == ""


def test_obtenir_ast_retourne_un_module():
    fichier = Fichier(code="x = 1\n", extension=".py")

    assert isinstance(fichier.obtenir_ast(), ast.Module)


def test_obtenir_ast_est_mis_en_cache():
    fichier = Fichier(code="x = 1\n", extension=".py")

    premier = fichier.obtenir_ast()
    second = fichier.obtenir_ast()

    assert second is premier


def test_obtenir_ast_fichier_non_python():
    fichier = Fichier(code="x = 1\n", extension=".txt")

    with pytest.raises(ValueError):
        fichier.obtenir_ast()


def test_obtenir_ast_code_invalide():
    fichier = Fichier(code="def f(:\n", extension=".py")

    with pytest.raises(SyntaxError):
        fichier.obtenir_ast()
