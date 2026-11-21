import json

import streamlit as st

from utils.affichage import afficher_audit, configurer_page
from utils.api_client import api_client
from utils.log_init import get_page_logger

configurer_page(layout="centered")
logger = get_page_logger("home")

# Réinitialise l'audit en mémoire
st.session_state["audit_id"] = None

st.title("Vérification de certificats")
st.write("Déposez le certificat à analyser.")

certificat = st.file_uploader(
    "Certificat",
    type=["json"],
)

st.write("Ou renseignez directement les informations importantes.")

certificat_key = st.text_input("Signature du certificat")
certificat_audit = st.number_input(
    "ID de l'audit correspondant au certificat", min_value=1, value=1
)
certificat_date = st.text_input("Date du certificat")

data_ok = (certificat is not None) or ((certificat_date != "") and (certificat_key != ""))
audit = None

if st.button("Vérifier certificat", type="primary", disabled=not data_ok):
    with st.spinner("Analyse en cours..."):
        if certificat is not None:
            try:
                contenu = json.loads(certificat.getvalue().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                st.error("Fichier illisible : le certificat doit être un JSON valide.")
        else:
            contenu = {}
            contenu["cle"] = certificat_key
            contenu["audit_id"] = certificat_audit
            contenu["date_delivrance"] = certificat_date

        data = {
            "signature": contenu["cle"],
            "id_audit": contenu["audit_id"],
            "date_delivrance": contenu["date_delivrance"],
        }

        # Envoyer le certificat à vérifier au backend
        reponse = api_client.post(
            "/audit/verif_certificat",
            json=data,
            timeout=60,
        )

    if reponse and reponse["status_code"] == 200:
        st.session_state["audit"] = reponse["data"]
        st.success("✅ Certificat authentique")
        audit = st.session_state.get("audit")
    elif reponse and reponse["status_code"] == 404:
        st.error("❌ Signature invalide")
    else:
        code = reponse["status_code"] if reponse else "aucune réponse"
        logger.error(f"Échec de l'analyse : {code}")
        st.error(
            f"L'analyse du certificat a échoué (code {code}). {reponse['data'] if reponse else ''}"
        )

if audit:
    st.title("Audit concerné :")
    afficher_audit(audit)
