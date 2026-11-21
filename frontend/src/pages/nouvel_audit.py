import hashlib
import hmac
import json
import os
import struct

import streamlit as st

from utils.affichage import afficher_audit, configurer_page
from utils.api_client import api_client
from utils.env_variables import load_environment_variables
from utils.log_init import get_page_logger

configurer_page(layout="centered")
logger = get_page_logger("home")

load_environment_variables()


# signature du fichier
def signer_fichiers(fichiers, cle_secrete: str) -> str:
    """Signe les fichiers envoyés par le frontend."""

    # Utiliser exactement le même encodage que le backend.
    elements = sorted(
        [(f.name, f.getvalue()) for f in fichiers],
        key=lambda element: element[0],
    )

    noms = [nom for nom, _ in elements]
    if len(noms) != len(set(noms)):
        raise ValueError("Deux fichiers portent le même nom.")

    contenu = bytearray()

    for nom, donnees in elements:
        nom_bytes = nom.encode("utf-8")

        contenu.extend(struct.pack(">Q", len(nom_bytes)))
        contenu.extend(nom_bytes)
        contenu.extend(struct.pack(">Q", len(donnees)))
        contenu.extend(donnees)

    return hmac.new(
        cle_secrete.encode("utf-8"),
        bytes(contenu),
        hashlib.sha256,
    ).hexdigest()


utilisateur = st.session_state.get("utilisateur")  # None si invité

st.title("Nouvel audit")
st.write("Déposez les fichiers de code à analyser.")

if utilisateur:
    st.caption(f"Connecté en tant que {utilisateur.get('name', '')} : vos audits sont enregistrés.")
else:
    st.info(
        "Vous utilisez l'application en invité : le résultat s'affiche, "
        "mais l'audit n'est pas enregistré."
    )
    col1, col2 = st.columns(2)
    if col1.button("Se connecter"):
        st.switch_page("pages/home.py")
    if col2.button("Créer un compte"):
        st.switch_page("pages/creer_compte.py")

# MODIFIÉ : on n'accepte que les types de fichiers que le backend sait lire
fichiers = st.file_uploader(
    "Fichiers (.py, requirements.txt, pyproject.toml, uv.lock, .zip)",
    type=["py", "txt", "toml", "lock", "zip"],
    accept_multiple_files=True,
)

n = st.number_input("Taille de l'entrée de référence (n)", min_value=1, value=500, step=100)

if st.button("Lancer l'audit", type="primary", disabled=not fichiers):
    with st.spinner("Analyse en cours..."):
        files = [
            ("liste_fichier", (f.name, f.getvalue(), f.type or "application/octet-stream"))
            for f in fichiers
        ]
        donnees = {"utilisateur_id": utilisateur["id"], "nb_entree": n} if utilisateur else None

        # F1 : Récupérer la clé secrète
        cle_secrete = os.getenv("HMAC_SECRET_KEY")

        # F1 : Calculer la signature HMAC
        signature = signer_fichiers(fichiers, cle_secrete)

        # Envoyer les fichiers et leur signature au backend
        reponse = api_client.post(
            "/audit/start_audit",
            files=files,
            data=donnees,
            headers={"X-HMAC-Signature": signature},
            timeout=60,
        )

    if reponse and reponse["status_code"] == 200:
        st.session_state["dernier_audit"] = reponse["data"]
    else:
        code = reponse["status_code"] if reponse else "aucune réponse"
        logger.error(f"Échec de l'audit : {code}")
        st.error(f"L'audit a échoué (code {code}). {reponse['data'] if reponse else ''}")


def recuperer_exports(id_audit: int) -> dict:
    """Récupère le certificat et le SBOM d'un audit, en les gardant en session."""
    cle = f"exports_{id_audit}"
    if cle not in st.session_state:
        st.session_state[cle] = {
            "certificat": api_client.get(f"/audit/{id_audit}/certificat"),
            "sbom": api_client.get(f"/audit/{id_audit}/sbom"),
        }
    return st.session_state[cle]


audit = st.session_state.get("dernier_audit")
if audit:
    st.divider()
    st.subheader("Résultat de l'audit")
    afficher_audit(audit, cle="nouvel_audit")
    id_audit = audit.get("id")

    if utilisateur and id_audit is not None:
        st.subheader("Certificat et SBOM")
        exports = recuperer_exports(id_audit)
        col_certif, col_sbom = st.columns(2)

        # --- Certificat ---
        rep_certif = exports["certificat"]
        if rep_certif["status_code"] == 200:
            certificat = rep_certif["data"]
            statut = certificat["statut"]

            if statut == "validé":
                st.success(f"Certificat : {statut} ✅")
            elif statut in ("échoué", "rejeté"):
                st.error(f"Certificat : {statut} ❌")
            else:
                st.warning(f"Certificat : {statut}")

            if certificat.get("motifs"):
                with st.expander("Motifs"):
                    for motif in certificat["motifs"]:
                        st.write(f"- {motif}")

            col_certif.download_button(
                "📄 Télécharger le certificat",
                data=json.dumps(certificat, ensure_ascii=False, indent=2),
                file_name=f"certificat_audit_{id_audit}.json",
                mime="application/json",
            )
        else:
            col_certif.error(f"Certificat indisponible (code {rep_certif['status_code']}).")

        # --- SBOM ---
        rep_sbom = exports["sbom"]
        if rep_sbom["status_code"] == 200:
            col_sbom.download_button(
                "📦 Télécharger le SBOM",
                data=json.dumps(rep_sbom["data"], ensure_ascii=False, indent=2),
                file_name=f"sbom_audit_{id_audit}.json",
                mime="application/json",
            )
        else:
            col_sbom.error(f"SBOM indisponible (code {rep_sbom['status_code']}).")
    elif not utilisateur:
        st.caption(
            "Audit non enregistré : connectez-vous pour conserver vos audits "
            "et télécharger le certificat et le SBOM."
        )
