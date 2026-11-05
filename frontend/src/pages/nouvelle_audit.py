import streamlit as st
from utils.auth import exiger_connexion

from utils.api_client import api_client

st.set_page_config(page_title="Nouvel audit", page_icon="🌱")
exiger_connexion()

st.title("Nouvel audit")
st.write("Déposez les fichiers de code à analyser.")

fichiers = st.file_uploader(
    "Fichiers (.py, requirements.txt, pyproject.toml)",
    accept_multiple_files=True,
)

if st.button("Lancer l'audit", type="primary", disabled=not fichiers):
    with st.spinner("Analyse en cours..."):
        try:
            reponse = api_client.post_files("/audits", fichiers)  # voir note ci-dessous
        except Exception as e:
            st.error(f"Connexion impossible : {e}")
            st.stop()

    if reponse and reponse["status_code"] == 200:
        st.session_state["audit_id"] = reponse["data"]["id"]
        st.switch_page("pages/detail_audit.py")
    else:
        st.error("L'audit a échoué, voir les logs.")
