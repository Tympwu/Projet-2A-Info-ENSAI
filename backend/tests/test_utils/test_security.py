"""Tests de la signature HMAC des soumissions (F1) et du hachage des mots de passe."""

import pytest

from utils.security import calculer_hmac, hash_mdp, preparer_contenu_hmac, verifier_hmac

FICHIERS = [("main.py", b"print('ok')\n"), ("requirements.txt", b"requests==2.31.0\n")]


def test_contenu_hmac_independant_de_l_ordre():
    """Client et serveur doivent obtenir le même message, quel que soit l'ordre d'envoi."""
    assert preparer_contenu_hmac(FICHIERS) == preparer_contenu_hmac(list(reversed(FICHIERS)))


def test_contenu_hmac_sans_ambiguite():
    """Les longueurs évitent qu'un découpage différent des mêmes octets donne le même message."""
    assert preparer_contenu_hmac([("ab", b"c")]) != preparer_contenu_hmac([("a", b"bc")])


def test_contenu_hmac_refuse_les_noms_en_double():
    with pytest.raises(ValueError):
        preparer_contenu_hmac([("a.py", b"1"), ("a.py", b"2")])


def test_signature_valide_acceptee():
    contenu = preparer_contenu_hmac(FICHIERS)
    signature = calculer_hmac(contenu, "cle-hmac-de-test")

    assert verifier_hmac(contenu, signature) is True


@pytest.mark.parametrize(

    "fichiers_recus",
    [
        pytest.param([("main.py", b"print('pirate')\n"), FICHIERS[1]], id="contenu modifie"),
        pytest.param(FICHIERS[:1], id="fichier retire"),
    ],
)
def test_soumission_modifiee_refusee(fichiers_recus):
    """Toute modification après signature est détectée."""
    signature = calculer_hmac(preparer_contenu_hmac(FICHIERS), "cle-hmac-de-test")

    assert verifier_hmac(preparer_contenu_hmac(fichiers_recus), signature) is False


def test_signature_avec_une_autre_cle_refusee():
    contenu = preparer_contenu_hmac(FICHIERS)

    assert verifier_hmac(contenu, calculer_hmac(contenu, "mauvaise-cle")) is False


def test_cle_hmac_absente(monkeypatch):
    monkeypatch.delenv("HMAC_SECRET_KEY")

    with pytest.raises(RuntimeError):
        verifier_hmac(b"contenu", "signature")


def test_hash_mdp_sale_par_le_nom():
    """Deux utilisateurs avec le même mot de passe n'ont pas le même hash."""
    assert hash_mdp("Secret123!", "alice") != hash_mdp("Secret123!", "bob")
    assert hash_mdp("Secret123!", "alice") == hash_mdp("Secret123!", "alice") 