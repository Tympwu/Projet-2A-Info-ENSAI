import base64
import hashlib
import hmac
import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def hash_mdp(mdp: str, name: str) -> str:
    """Hash un mot de passe en utilisant un algorithme SHA-256.
    Args:
        mdp (str): Le mot de passe à hash.
        name (str): Un paramètre à rajouter en plus pour être le sel du mot de passe
    Returns:
        str: Le string hexadecimal correspondant.
    """
    salted_mdp = f"{name}{mdp}"
    return hashlib.sha256(salted_mdp.encode()).hexdigest()


def preparer_contenu_hmac(fichiers: list[tuple[str, bytes]]) -> bytes:
    """Construit un message déterministe à partir des fichiers soumis."""

    # Trier les fichiers pour obtenir le même résultat des deux côtés.
    fichiers_tries = sorted(fichiers, key=lambda element: element[0])

    # Refuser les noms identiques pour éviter les ambiguïtés.
    noms = [nom for nom, _ in fichiers_tries]
    if len(noms) != len(set(noms)):
        raise ValueError("Deux fichiers portent le même nom.")

    contenu = bytearray()

    for nom, donnees in fichiers_tries:
        nom_bytes = nom.encode("utf-8")

        # Ajouter les longueurs pour séparer les noms et les contenus.
        contenu.extend(struct.pack(">Q", len(nom_bytes)))
        contenu.extend(nom_bytes)
        contenu.extend(struct.pack(">Q", len(donnees)))
        contenu.extend(donnees)

    return bytes(contenu)


def calculer_hmac(contenu: bytes, cle_secrete: str) -> str:
    """Calcule une signature HMAC-SHA256."""

    return hmac.new(
        cle_secrete.encode("utf-8"),
        contenu,
        hashlib.sha256,
    ).hexdigest()


def verifier_hmac(contenu: bytes, signature: str) -> bool:
    """Vérifie la signature à partir de la clé du backend."""

    cle_secrete = os.getenv("HMAC_SECRET_KEY")

    if not cle_secrete:
        raise RuntimeError("HMAC_SECRET_KEY non configurée.")

    signature_attendue = calculer_hmac(contenu, cle_secrete)

    # Comparaison résistante aux attaques temporelles.
    return hmac.compare_digest(signature_attendue, signature)


def _lire_cle_pem(nom: str) -> bytes:
    """Lit une clé PEM depuis l'environnement (les '\\n' littéraux sont convertis en retours à la ligne)."""
    valeur = os.getenv(nom)
    if not valeur:
        raise RuntimeError(f"{nom} non configurée.")
    return valeur.replace("\\n", "\n").encode()


def crypter_certificat(message: str) -> str:
    """Fonction permettant de signer des données pour valider le certificat"""
    private_key = serialization.load_pem_private_key(_lire_cle_pem("PRIVATE_KEY"), password=None)
    sig = private_key.sign(
        message.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode()


def decrypt_certificat(message: str, signature_b64: str) -> bool:
    """Fonction permettant de vérifier la signature d'un certificat"""
    public_key = serialization.load_pem_public_key(_lire_cle_pem("PUBLIC_KEY"))
    try:
        public_key.verify(
            base64.b64decode(signature_b64),
            message.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
