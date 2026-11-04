"""
Tests de la classe Analyse_fichier (configuration et estimation de la complexité).

Lancer : pytest tests/test_analyse_fichier.py -v
Si les imports échouent, adapte les deux lignes `from ... import` à l'arborescence du projet.
"""
import ast

import pytest
from service.analyse_fichier import Analyse_fichier, AnalyseurComplexite

from business_object.fichier import Fichier


def boucles_imbriquees(n: int) -> str:
    """Code Python avec `n` boucles `for` imbriquées (n = 0 : aucune boucle)."""
    lignes = ["def f(l):"]
    for i in range(n):
        lignes.append("    " * (i + 1) + "for x in l:")
    lignes.append("    " * (n + 1) + "pass")
    return "\n".join(lignes) + "\n"


def creer_fichier(tmp_path, contenu: str, nom: str = "exemple.py") -> Fichier:
    """Écrit `contenu` dans un vrai fichier temporaire et retourne l'objet Fichier."""
    chemin = tmp_path / nom
    chemin.write_text(contenu, encoding="utf-8")
    return Fichier(chemin=str(chemin))


@pytest.fixture
def sans_dotenv(monkeypatch):
    """Ne lit pas un vrai fichier .env : le test ne dépend pas de la machine."""
    monkeypatch.setattr("service.analyse_fichier.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("OSV_API_URL", raising=False)


# ---------- Configuration ----------

def test_url_par_defaut(sans_dotenv):
    assert Analyse_fichier().api_url_OSV == "https://api.osv.dev/v1/query"


def test_url_lue_dans_la_variable_d_environnement(sans_dotenv, monkeypatch):
    monkeypatch.setenv("OSV_API_URL", "https://exemple.test/v1/query")
    assert Analyse_fichier().api_url_OSV == "https://exemple.test/v1/query"


def test_rechargement_prend_la_nouvelle_valeur(sans_dotenv, monkeypatch):
    analyseur = Analyse_fichier()
    monkeypatch.setenv("OSV_API_URL", "https://autre.test/v1/query")
    analyseur.load_environment_variables()
    assert analyseur.api_url_OSV == "https://autre.test/v1/query"


# ---------- AnalyseurComplexite : profondeur des boucles ----------

@pytest.mark.parametrize(
    "source, profondeur",
    [
        pytest.param(boucles_imbriquees(0), 0, id="aucune boucle"),
        pytest.param(boucles_imbriquees(1), 1, id="une boucle"),
        pytest.param(boucles_imbriquees(3), 3, id="trois boucles imbriquées"),
        pytest.param("def f(n):\n    while n:\n        n -= 1\n", 1, id="while"),
        pytest.param(
            "def f(l):\n    while l:\n        for x in l:\n            pass\n", 2,
            id="for dans while"),
        pytest.param("def f(l):\n    for a in l:\n        pass\n    for b in l:\n        pass\n", 1,
                     id="deux boucles à la suite : pas imbriquées"),
        pytest.param("def a(l):\n    for x in l:\n        pass\n" + boucles_imbriquees(2), 2,
                     id="deux fonctions : la pire compte"),
    ],
)
def test_profondeur_mesuree(source, profondeur):
    analyseur = AnalyseurComplexite()
    analyseur.visit(ast.parse(source))
    assert analyseur.max_imbrication == profondeur
    assert analyseur.boucles_imbriquees is (profondeur >= 2)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "def f(l):\n    return [x for a in l for x in a]\n", id="compréhension imbriquée"),
        pytest.param(
            "def f(l):\n    return sorted(l)\n", id="tri"),
        pytest.param(
            "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n", id="récursion"),
    ],
)
def test_limites_connues_non_detectees(source):
    """Limite choisie : seuls `for` et `while` sont comptés. À mettre à jour si on étend l'analyse.
    """
    analyseur = AnalyseurComplexite()
    analyseur.visit(ast.parse(source))
    assert analyseur.max_imbrication == 0


# ---------- analyser_complexite_code ----------

@pytest.mark.parametrize(
    "boucles, attendu",
    [(0, "O(1)"), (1, "O(n)"), (2, "O(n²)"), (3, "O(n³)"), (4, "O(n^k), k > 3")],
)
def test_libelle_retourne_et_ecrit_dans_le_fichier(tmp_path, boucles, attendu):
    fichier = creer_fichier(tmp_path, boucles_imbriquees(boucles))
    assert Analyse_fichier().analyser_complexite_code(fichier) == attendu
    assert fichier.complexite == attendu


@pytest.mark.parametrize(
    "nom, contenu",
    [
        pytest.param("script.js", "for(;;){}", id="fichier non Python"),
        pytest.param("code.py", "def (:\n", id="syntaxe invalide"),
    ],
)
def test_fichier_non_analysable_donne_none(tmp_path, nom, contenu):
    fichier = creer_fichier(tmp_path, contenu, nom=nom)
    assert Analyse_fichier().analyser_complexite_code(fichier) is None
    assert fichier.complexite is None


def test_fichier_introuvable_leve_une_erreur(tmp_path):
    fichier = Fichier(chemin=str(tmp_path / "absent.py"))
    with pytest.raises(FileNotFoundError):
        Analyse_fichier().analyser_complexite_code(fichier)


def test_meme_instance_pour_plusieurs_fichiers_sans_melange(tmp_path):
    analyseur = Analyse_fichier()
    lourd = creer_fichier(tmp_path, boucles_imbriquees(2), nom="lourd.py")
    leger = creer_fichier(tmp_path, boucles_imbriquees(0), nom="leger.py")
    assert analyseur.analyser_complexite_code(lourd) == "O(n²)"
    assert analyseur.analyser_complexite_code(leger) == "O(1)"


def test_libelles_du_service_presents_dans_l_echelle_de_fichier():
    libelles = set(Analyse_fichier.LIBELLES_PAR_PROFONDEUR.values())
    libelles.add(Analyse_fichier.LIBELLE_AU_DELA)
    assert libelles <= set(Fichier.ECHELLE_COMPLEXITE)
