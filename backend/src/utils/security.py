import hashlib
import hmac
import os
import struct
from fastapi import Header, HTTPException

from dao.utilisateur_dao import UtilisateurDao


def hash_password(password: str, salt: str = "") -> str:
    """Hashes a password using the SHA-256 algorithm.
    Args:
        password (str): The plain text password to be hashed.
        salt (str, optional): A string added to the password before hashing
            to protect against rainbow table attacks.
    Returns:
        str: The resulting hexadecimal hash string.
    """
    password_bytes = password.encode("utf-8") + salt.encode("utf-8")
    hash_object = hashlib.sha256(password_bytes)
    return hash_object.hexdigest()


def verify_token(x_auth_token=Header(None)) -> UtilisateurDao:
    """Verifies the authenticity of a player via the provided auth token.

    This function checks if a token is present in the request headers and
    validates it against the database.
    Args:
        x_auth_token (str, optional): The token extracted from the
            'X-Auth-Token' HTTP header. Defaults to None.
    Returns:
        Utilisateur object associated with the valid token.
    Raises:
        HTTPException: 401 error if the token is missing.
        HTTPException: 401 error if the token is not found in the database.
    """
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="Missing token.")

    player = UtilisateurDao().find_by_token(x_auth_token)
    if not player:
        raise HTTPException(status_code=401, detail="Invalid token.")

    return player

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
