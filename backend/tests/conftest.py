import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from utils.env_variables import load_environment_variables

load_environment_variables()

# Paire de clés RSA générée une seule fois pour toute la session de tests :
# les tests ne dépendent ainsi ni du fichier .env ni des vraies clés du projet.
_CLE_PRIVEE_TEST = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_KEY_TEST = _CLE_PRIVEE_TEST.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()
PUBLIC_KEY_TEST = (
    _CLE_PRIVEE_TEST.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)


@pytest.fixture(autouse=True)
def cles_de_test(monkeypatch):
    """Fournit à chaque test les clés de signature des certificats et la clé HMAC."""
    monkeypatch.setenv("PRIVATE_KEY", PRIVATE_KEY_TEST)
    monkeypatch.setenv("PUBLIC_KEY", PUBLIC_KEY_TEST)
    monkeypatch.setenv("HMAC_SECRET_KEY", "cle-hmac-de-test")
