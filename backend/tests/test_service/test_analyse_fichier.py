"""Tests de Analyse_fichier : configuration, complexité, anti-patterns, CO2 et vulnérabilités (OSV)."""

import ast
import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from business_object.dependance import Dependances
from business_object.fichier import Fichier
from service.analyse_fichier import Analyse_fichier, AnalyseurComplexite
from utils.singleton import Singleton

CVSS3_CRITIQUE = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"  # score 9.8


def boucles_imbriquees(n: int) -> str:
    """Code Python avec `n` boucles `for` imbriquées (n = 0 : aucune boucle)."""
    lignes = ["def f(l):"]
    for i in range(n):
        lignes.append("    " * (i + 1) + "for x in l:")
    lignes.append("    " * (n + 1) + "pass")
    return "\n".join(lignes) + "\n"


def fichier_py(code: str) -> Fichier:
    return Fichier(code=code, extension=".py")


@pytest.fixture(autouse=True)
def sans_dotenv(monkeypatch):
    """Ne lit pas un vrai fichier .env : les tests ne dépendent pas de la machine."""
    monkeypatch.setattr("service.analyse_fichier.load_dotenv", lambda *args, **kwargs: None)
    for variable in ("OSV_API_URL", "PUISSANCE_MACHINE_W", "INTENSITE_CARBONE_G_KWH"):
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture(autouse=True)
def nouvelle_instance():
    """Analyse_fichier est un singleton (avec un cache des réponses OSV) : chaque test
    repart d'une instance neuve, sinon la configuration et le cache d'un test
    précédent fausseraient le suivant."""
    Singleton._instances.pop(Analyse_fichier, None)
    yield
    Singleton._instances.pop(Analyse_fichier, None)


@pytest.fixture
def analyseur():
    return Analyse_fichier()


# ---------- Configuration ----------


def test_valeurs_par_defaut(analyseur):
    assert analyseur.api_url_OSV == "https://api.osv.dev/v1/query"
    assert analyseur.puissance_machine == 15.0
    assert analyseur.intensite_carbone == 29.0


def test_configuration_lue_dans_l_environnement(monkeypatch):
    monkeypatch.setenv("OSV_API_URL", "https://exemple.test/v1/query")
    monkeypatch.setenv("PUISSANCE_MACHINE_W", "20")
    monkeypatch.setenv("INTENSITE_CARBONE_G_KWH", "50")

    analyseur = Analyse_fichier()

    assert analyseur.api_url_OSV == "https://exemple.test/v1/query"
    assert analyseur.puissance_machine == 20.0
    assert analyseur.intensite_carbone == 50.0


def test_rechargement_prend_la_nouvelle_valeur(analyseur, monkeypatch):
    monkeypatch.setenv("OSV_API_URL", "https://autre.test/v1/query")
    analyseur.load_environment_variables()

    assert analyseur.api_url_OSV == "https://autre.test/v1/query"


@pytest.mark.parametrize("url", ["http://api.osv.dev/v1/query", "file:///etc/passwd"])
def test_url_osv_non_https_refusee(monkeypatch, url):
    """Seule une adresse https est acceptée pour interroger OSV."""
    monkeypatch.setenv("OSV_API_URL", url)

    with pytest.raises(ValueError, match="https"):
        Analyse_fichier()


@pytest.mark.parametrize("variable", ["PUISSANCE_MACHINE_W", "INTENSITE_CARBONE_G_KWH"])
def test_configuration_non_numerique_refusee(monkeypatch, variable):
    monkeypatch.setenv(variable, "beaucoup")

    with pytest.raises(ValueError):
        Analyse_fichier()


# ---------- AnalyseurComplexite : profondeur des boucles ----------


@pytest.mark.parametrize(
    "source, profondeur",
    [
        pytest.param(boucles_imbriquees(0), 0, id="aucune boucle"),
        pytest.param(boucles_imbriquees(1), 1, id="une boucle"),
        pytest.param(boucles_imbriquees(3), 3, id="trois boucles imbriquées"),
        pytest.param("def f(n):\n    while n:\n        n -= 1\n", 1, id="while"),
        pytest.param(
            "def f(l):\n    while l:\n        for x in l:\n            pass\n",
            2,
            id="for dans while",
        ),
        pytest.param(
            "def f(l):\n    for a in l:\n        pass\n    for b in l:\n        pass\n",
            1,
            id="deux boucles à la suite : pas imbriquées",
        ),
        pytest.param(
            "def a(l):\n    for x in l:\n        pass\n" + boucles_imbriquees(2),
            2,
            id="deux fonctions : la pire compte",
        ),
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
        pytest.param("def f(l):\n    return [x for a in l for x in a]\n", id="compréhension"),
        pytest.param("def f(l):\n    return sorted(l)\n", id="tri"),
        pytest.param(
            "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n", id="récursion"
        ),
    ],
)
def test_limites_connues_non_detectees(source):
    """Limite choisie : seuls `for` et `while` sont comptés dans la complexité."""
    analyseur = AnalyseurComplexite()
    analyseur.visit(ast.parse(source))

    assert analyseur.max_imbrication == 0


# ---------- analyser_complexite_code ----------


@pytest.mark.parametrize("boucles", [0, 1, 2, 4])
def test_complexite_retournee_et_ecrite_dans_le_fichier(analyseur, boucles):
    fichier = fichier_py(boucles_imbriquees(boucles))

    assert analyseur.analyser_complexite_code(fichier) == boucles
    assert fichier.complexite == boucles


@pytest.mark.parametrize(
    "fichier",
    [
        pytest.param(Fichier(code="requests==2.31.0", extension=".txt"), id="non Python"),
        pytest.param(Fichier(code="def (:\n", extension=".py"), id="syntaxe invalide"),
    ],
)
def test_fichier_non_analysable_donne_none(analyseur, fichier):
    assert analyseur.analyser_complexite_code(fichier) is None
    assert fichier.complexite is None


def test_meme_instance_pour_plusieurs_fichiers_sans_melange(analyseur):
    lourd = fichier_py(boucles_imbriquees(2))
    leger = fichier_py(boucles_imbriquees(0))

    assert analyseur.analyser_complexite_code(lourd) == 2
    assert analyseur.analyser_complexite_code(leger) == 0


# ---------- detecter_anti_patterns ----------


def test_anti_pattern_boucles_imbriquees(analyseur):
    assert analyseur.detecter_anti_patterns(fichier_py(boucles_imbriquees(2))) == [
        "Boucles imbriquées"
    ]


def test_anti_pattern_recursivite_directe(analyseur):
    code = "def fact(n):\n    return 1 if n == 0 else n * fact(n - 1)\n"

    assert analyseur.detecter_anti_patterns(fichier_py(code)) == [
        "Récursivité directe dans la fonction fact"
    ]


def test_anti_pattern_recursivite_par_self(analyseur):
    code = "class A:\n    def parcourir(self, n):\n        return self.parcourir(n - 1)\n"

    assert analyseur.detecter_anti_patterns(fichier_py(code)) == [
        "Récursivité directe dans la fonction parcourir"
    ]


def test_aucun_anti_pattern(analyseur):
    assert analyseur.detecter_anti_patterns(fichier_py(boucles_imbriquees(1))) == []


def test_anti_patterns_fichier_non_python(analyseur):
    assert analyseur.detecter_anti_patterns(Fichier(code="", extension=".txt")) is None


# ---------- Estimation des émissions (F3) ----------


def test_calculer_nombre_operations(analyseur):
    fichier = fichier_py("")
    fichier.complexite = 2

    assert analyseur.calculer_nombre_operations(fichier, 10) == 100


@pytest.mark.parametrize(
    "complexite, taille",
    [
        pytest.param(2, 0, id="taille nulle"),
        pytest.param(None, 10, id="complexité inconnue"),
        pytest.param(-1, 10, id="complexité négative"),
    ],
)
def test_calculer_nombre_operations_invalide(analyseur, complexite, taille):
    fichier = fichier_py("")
    fichier.complexite = complexite

    with pytest.raises(ValueError):
        analyseur.calculer_nombre_operations(fichier, taille)


def test_calculer_emission(analyseur):
    """1 000 000 d'opérations à 1 000 000 op/s = 1 s à 3 600 W = 1 Wh = 0,001 kWh."""
    analyseur.vitesse_machine = 1_000_000  # fixé pour ne pas mesurer la machine du test
    analyseur.puissance_machine = 3600
    analyseur.intensite_carbone = 50
    fichier = fichier_py("")

    emission = analyseur.calculer_emissionCO2e(fichier, 1_000_000)

    assert emission == pytest.approx(0.05)  # 0,001 kWh × 50 gCO2e/kWh
    assert fichier.emissionCO2 == emission


@pytest.mark.parametrize(
    "attribut, valeur",
    [("puissance_machine", 0), ("pue", 0.5), ("intensite_carbone", -1), ("vitesse_machine", -1)],
)
def test_calculer_emission_parametre_invalide(analyseur, attribut, valeur):
    analyseur.vitesse_machine = 1_000_000
    setattr(analyseur, attribut, valeur)

    with pytest.raises(ValueError):
        analyseur.calculer_emissionCO2e(fichier_py(""), 100)


def test_calculer_emission_nombre_operations_negatif(analyseur):
    with pytest.raises(ValueError):
        analyseur.calculer_emissionCO2e(fichier_py(""), -1)


def test_estimer_emission_fichier(analyseur):
    analyseur.vitesse_machine = 1_000_000
    fichier = fichier_py(boucles_imbriquees(2))

    emission = analyseur.estimer_emission_fichier(fichier, 1000)

    attendu = (1000**2 / 1_000_000) * 15.0 / 3_600_000 * 29.0
    assert emission == pytest.approx(attendu)
    assert fichier.complexite == 2


def test_estimer_emission_fichier_non_analysable(analyseur):
    with pytest.raises(ValueError):
        analyseur.estimer_emission_fichier(Fichier(code="", extension=".txt"), 1000)


# ---------- Scores des vulnérabilités ----------


@pytest.mark.parametrize(
    "texte, attendu",
    [
        pytest.param("7.5", 7.5, id="nombre"),
        pytest.param("12", None, id="nombre hors échelle"),
        pytest.param(CVSS3_CRITIQUE, 9.8, id="vecteur CVSS 3"),
        pytest.param("CVSS:3.1/AV:Z", None, id="vecteur invalide"),
        pytest.param("n'importe quoi", None, id="texte"),
    ],
)
def test_convertir_score(texte, attendu):
    assert Analyse_fichier._convertir_score(texte) == attendu


def test_score_vulnerabilite_garde_le_plus_grand(analyseur):
    fiche = {"severity": [{"score": "5.0"}, {"score": CVSS3_CRITIQUE}]}

    assert analyseur._score_vulnerabilite(fiche) == 9.8


def test_score_vulnerabilite_par_etiquette(analyseur):
    fiche = {"database_specific": {"severity": "high"}}

    assert analyseur._score_vulnerabilite(fiche) == 8.0


def test_score_vulnerabilite_inconnu(analyseur):
    assert analyseur._score_vulnerabilite({"id": "GHSA-x"}) is None


# ---------- Appel à l'API OSV (simulé) ----------


def reponse_osv(donnees: dict):
    """Fausse réponse HTTP utilisable dans un `with urlopen(...) as reponse`."""
    return io.BytesIO(json.dumps(donnees).encode("utf-8"))


def test_interroger_osv_envoie_nom_version_et_suit_les_pages(analyseur):
    pages = [
        reponse_osv({"vulns": [{"id": "A"}], "next_page_token": "page2"}),
        reponse_osv({"vulns": [{"id": "B"}]}),
    ]
    with patch("service.analyse_fichier.urllib.request.urlopen", side_effect=pages) as urlopen:
        fiches = analyseur._interroger_osv(
            Dependances(nom="requests", version="2.19.0", auteur=None)
        )

    assert [f["id"] for f in fiches] == ["A", "B"]
    premier_corps = json.loads(urlopen.call_args_list[0].args[0].data)
    assert premier_corps["package"] == {"name": "requests", "ecosystem": "PyPI"}
    assert premier_corps["version"] == "2.19.0"
    second_corps = json.loads(urlopen.call_args_list[1].args[0].data)
    assert second_corps["page_token"] == "page2"


def test_analyse_dependances_score_et_vulnerabilites_retenues(analyseur):
    fichier = Fichier(code="requests==2.19.0\nflask==3.0.0\n", extension=".txt")
    fiches_par_nom = {
        "requests": [
            {"id": "GRAVE", "summary": "faille grave", "severity": [{"score": CVSS3_CRITIQUE}]},
            {"id": "MOYENNE", "severity": [{"score": "5.0"}]},
            {"id": "INCONNUE"},  # sans gravité : ignorée
        ],
        "flask": [],
    }
    with patch.object(analyseur, "_interroger_osv", side_effect=lambda d: fiches_par_nom[d.nom]):
        assert analyseur.analyse_dependances(fichier) is True

    assert fichier.score == 9.8
    assert [v.description for v in fichier.liste_vulnerabilites] == ["GRAVE : faille grave"]


def test_analyse_dependances_sans_dependance(analyseur):
    fichier = fichier_py("import os\n")

    assert analyseur.analyse_dependances(fichier) is True
    assert fichier.score == 0.0
    assert fichier.liste_vulnerabilites == []


def test_analyse_dependances_api_injoignable(analyseur):
    fichier = Fichier(code="requests==2.19.0\n", extension=".txt")
    erreur = urllib.error.URLError("pas de réseau")
    with patch.object(analyseur, "_interroger_osv", side_effect=erreur):
        assert analyseur.analyse_dependances(fichier) is False

    assert fichier.score is None
    assert fichier.liste_vulnerabilites is None


def test_analyse_dependances_fichier_illisible(analyseur):
    fichier = Fichier(code="", extension=".js")

    assert analyseur.analyse_dependances(fichier) is False
    assert fichier.score is None


def test_interroger_osv_met_en_cache_par_nom_et_version(analyseur):
    """Une même dépendance n'est demandée qu'une fois ; une autre version est redemandée."""
    reponses = [reponse_osv({"vulns": [{"id": "A"}]}), reponse_osv({"vulns": []})]
    with patch("service.analyse_fichier.urllib.request.urlopen", side_effect=reponses) as urlopen:
        ancienne = Dependances(nom="requests", version="2.19.0", auteur=None)
        premiere = analyseur._interroger_osv(ancienne)
        seconde = analyseur._interroger_osv(ancienne)
        recente = analyseur._interroger_osv(
            Dependances(nom="requests", version="2.32.3", auteur=None)
        )

    assert premiere == seconde == [{"id": "A"}]
    assert recente == []
    assert urlopen.call_count == 2
