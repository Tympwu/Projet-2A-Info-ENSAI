import streamlit as st

from utils.affichage import afficher_audit
from utils.api_client import api_client
from utils.auth import exiger_connexion

st.set_page_config(page_title="Historique", page_icon="🌱")
utilisateur = exiger_connexion()

st.title("Mes audits")

reponse = api_client.get(f"/historic/{utilisateur['id']}")
if not reponse or reponse["status_code"] != 200:
    st.error("Impossible de charger l'historique.")
    st.stop()

audits = reponse["data"].get("audits", [])
if not audits:
    st.info("Vous n'avez pas encore d'audit enregistré.")

for a in audits:
    with st.expander(f"Audit n°{a['id']} · {a.get('date', '')} · {a.get('statut', '')}"):
        afficher_audit(a, cle=f"audit_{a['id']}")
