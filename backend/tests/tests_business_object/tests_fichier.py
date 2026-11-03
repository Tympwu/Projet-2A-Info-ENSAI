"""
Tests de la classe Fichier.

Lancer : pytest tests/test_business_object/test_fichier.py -v
Si l'import échoue, adapte la ligne `from business_object.fichier import Fichier`.
"""
import ast
from types import SimpleNamespace

import pytest

from business_object.fichier import Fichier


def creer_fichier(tmp_path, contenu: str, nom: str = "exemple.py", **options) -> Fichier:
    """Écrit `contenu` dans un vrai fichier temporaire et retourne l'objet Fichier."""
    chemin = tmp_path / nom
    chemin.write_text(contenu, encoding="utf-8")
    return Fichier(chemin=str(chemin), **options)


def vulnerabilite(critique: bool):
    """Fausse vulnérabilité : seule la méthode est_critique() est utilisée par Fichier."""
    return SimpleNamespace(est_critique=lambda: critique)


# ---------- Création ----------

def test_valeurs_par_defaut():
    fichier = Fichier(chemin="code.py")
    assert fichier.id is None
    assert fichier.liste_vulnerabilites is None
    assert fichier.liste_dependances is None
    assert fichier.complexite is None
    assert fichier.score is None
    assert fichier.emissionCO2 is None
    assert fichier.AST_analyse is None


def test_extension_deduite_du_chemin():
    assert Fichier(chemin="dossier/code.py").extension == ".py"


def test_extension_fournie_prioritaire_sur_le_chemin():
    assert Fichier(chemin="code.py", extension=".js").extension == ".js"


def test_echelle_complexite_sans_doublon_et_commence_par_o1():
    echelle = Fichier.ECHELLE_COMPLEXITE
    assert echelle[0] == "O(1)"
    assert len(set(echelle)) == len(echelle)


# ---------- Lecture ----------

def test_lire_contenu(tmp_path):
    fichier = creer_fichier(tmp_path, "ligne 1\nligne 2\n")
    assert fichier.lire_contenu() == "ligne 1\nligne 2\n"


def test_lire_contenu_fichier_introuvable(tmp_path):
    with pytest.raises(FileNotFoundError):
        Fichier(chemin=str(tmp_path / "absent.py")).lire_contenu()


def test_lire_contenu_encodage_illisible(tmp_path):
    chemin = tmp_path / "binaire.py"
    chemin.write_bytes(b"x = '\xff\xfe'\n")
    with pytest.raises(UnicodeDecodeError):
        Fichier(chemin=str(chemin)).lire_contenu()


def test_lire_ligne_sans_saut_de_ligne_final(tmp_path):
    fichier = creer_fichier(tmp_path, "premiere\ndeuxieme\n")
    assert fichier.lire_ligne(1) == "premiere"
    assert fichier.lire_ligne(2) == "deuxieme"


@pytest.mark.parametrize("numero, erreur", [(0, ValueError), (-1, ValueError), (3, IndexError)])
def test_lire_ligne_numero_invalide(tmp_path, numero, erreur):
    fichier = creer_fichier(tmp_path, "premiere\ndeuxieme\n")
    with pytest.raises(erreur):
        fichier.lire_ligne(numero)


# ---------- Arbre syntaxique ----------

def test_obtenir_ast_construit_puis_conserve_l_arbre(tmp_path):
    fichier = creer_fichier(tmp_path, "x = 1\n")
    arbre = fichier.obtenir_ast()
    assert isinstance(arbre, ast.Module)
    assert fichier.AST_analyse is arbre
    assert fichier.obtenir_ast() is arbre


def test_obtenir_ast_reutilise_un_arbre_deja_fourni():
    arbre = ast.parse("x = 1")
    fichier = Fichier(chemin="n_existe_pas.py", AST_analyse=arbre)
    assert fichier.obtenir_ast() is arbre


def test_obtenir_ast_refuse_un_fichier_non_python(tmp_path):
    fichier = creer_fichier(tmp_path, "texte", nom="notes.txt")
    with pytest.raises(ValueError):
        fichier.obtenir_ast()


def test_obtenir_ast_signale_une_syntaxe_invalide(tmp_path):
    fichier = creer_fichier(tmp_path, "def (:\n")
    with pytest.raises(SyntaxError):
        fichier.obtenir_ast()


def test_obtenir_ast_signale_un_fichier_introuvable(tmp_path):
    with pytest.raises(FileNotFoundError):
        Fichier(chemin=str(tmp_path / "absent.py")).obtenir_ast()


# ---------- Dépendances ----------

def test_dependances_externes_triees_sans_doublon_ni_bibliotheque_standard(tmp_path):
    source = (
        "import os\n"
        "import sys\n"
        "import requests\n"
        "import numpy.linalg\n"
        "from flask import Flask\n"
        "from . import local\n"
        "from .autre import chose\n"
        "import requests\n"
    )
    fichier = creer_fichier(tmp_path, source)
    noms = [d.nom for d in fichier.obtenir_dependances_fichier()]
    assert noms == ["flask", "numpy", "requests"]
    assert fichier.liste_dependances is not None


def test_dependances_vides_sans_import_externe(tmp_path):
    fichier = creer_fichier(tmp_path, "import os\nx = 1\n")
    assert fichier.obtenir_dependances_fichier() == []


def test_dependances_fichier_non_python(tmp_path):
    fichier = creer_fichier(tmp_path, "import requests", nom="notes.txt")
    assert fichier.obtenir_dependances_fichier() == []
    assert fichier.liste_dependances == []


# ---------- Risque ----------

def test_est_a_risque_leve_une_erreur_si_pas_encore_analyse():
    with pytest.raises(ValueError):
        Fichier(chemin="code.py").est_a_risque()


@pytest.mark.parametrize(
    "criticites, attendu",
    [
        pytest.param([], False, id="analysé sans vulnérabilité"),
        pytest.param([False, False], False, id="aucune critique"),
        pytest.param([False, True], True, id="une critique suffit"),
    ],
)
def test_est_a_risque(criticites, attendu):
    fichier = Fichier(
        chemin="code.py", liste_vulnerabilites=[vulnerabilite(c) for c in criticites]
    )
    assert fichier.est_a_risque() is attendu
