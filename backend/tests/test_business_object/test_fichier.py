import ast

import pytest

from business_object.fichier import Fichier
from business_object.vulnerabilite import Vulnerabilite


def test_init_deduit_extension_du_chemin():
    # Préparer et agir : on crée un fichier sans préciser l'extension
    fichier = Fichier(chemin="dossier/script.py")
    # Vérifier : l'extension a été déduite du chemin
    assert fichier.extension == ".py"


def test_init_garde_extension_fournie():
    fichier = Fichier(chemin="dossier/script.py", extension=".txt")
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
    fichier = Fichier(chemin="a.py")  # liste_vulnerabilites vaut None
    with pytest.raises(ValueError):
        fichier.est_a_risque()


def test_est_a_risque_avec_une_vulnerabilite_critique():
    vulnerabilites = [
        Vulnerabilite(description="faille mineure", score_danger=3.0),
        Vulnerabilite(description="faille grave", score_danger=9.8),
    ]
    fichier = Fichier(chemin="a.py", liste_vulnerabilites=vulnerabilites)
    assert fichier.est_a_risque() is True


def test_est_a_risque_sans_vulnerabilite():
    fichier = Fichier(chemin="a.py", liste_vulnerabilites=[])
    assert fichier.est_a_risque() is False


def test_est_a_risque_sans_vulnerabilite_critique():
    vulnerabilites = [
        Vulnerabilite(description="faille mineure", score_danger=3.0),
        Vulnerabilite(description="faille élevée", score_danger=8.9),
    ]
    fichier = Fichier(chemin="a.py", liste_vulnerabilites=vulnerabilites)
    assert fichier.est_a_risque() is False


def test_lire_contenu_retourne_tout_le_texte(tmp_path):
    chemin = tmp_path / "a.py"
    chemin.write_text("x = 1\ny = 2\n", encoding="utf-8")
    fichier = Fichier(chemin=str(chemin))
    assert fichier.lire_contenu() == "x = 1\ny = 2\n"


def test_lire_contenu_fichier_inexistant(tmp_path):
    fichier = Fichier(chemin=str(tmp_path / "absent.py"))
    with pytest.raises(FileNotFoundError):
        fichier.lire_contenu()


def test_lire_ligne_retourne_la_ligne_sans_saut(tmp_path):
    chemin = tmp_path / "a.txt"
    chemin.write_text("premiere\ndeuxieme\ntroisieme\n", encoding="utf-8")
    fichier = Fichier(chemin=str(chemin))
    assert fichier.lire_ligne(2) == "deuxieme"


def test_lire_ligne_numero_trop_petit(tmp_path):
    chemin = tmp_path / "a.txt"
    chemin.write_text("premiere\n", encoding="utf-8")
    fichier = Fichier(chemin=str(chemin))
    with pytest.raises(ValueError):
        fichier.lire_ligne(0)


def test_lire_ligne_numero_trop_grand(tmp_path):
    chemin = tmp_path / "a.txt"
    chemin.write_text("premiere\ndeuxieme\n", encoding="utf-8")
    fichier = Fichier(chemin=str(chemin))
    with pytest.raises(IndexError):
        fichier.lire_ligne(3)


@pytest.fixture
# pour créer des fichiers de test
def creer_fichier(tmp_path):
    def _creer(nom, contenu=""):
        chemin = tmp_path / nom
        chemin.write_text(contenu, encoding="utf-8")
        return Fichier(chemin=str(chemin))
    return _creer


def test_obtenir_ast_retourne_un_module(creer_fichier):
    fichier = creer_fichier("a.py", "x = 1\n")
    assert isinstance(fichier.obtenir_ast(), ast.Module)


def test_obtenir_ast_est_mis_en_cache(creer_fichier, tmp_path):
    fichier = creer_fichier("a.py", "x = 1\n")
    premier = fichier.obtenir_ast()
    (tmp_path / "a.py").unlink()  # on supprime le fichier du disque
    assert fichier.obtenir_ast() is premier


def test_obtenir_ast_fichier_non_python(creer_fichier):
    fichier = creer_fichier("notes.txt", "x = 1\n")
    with pytest.raises(ValueError):
        fichier.obtenir_ast()


def test_obtenir_ast_code_invalide(creer_fichier):
    fichier = creer_fichier("a.py", "def f(:\n")
    with pytest.raises(SyntaxError):
        fichier.obtenir_ast()
