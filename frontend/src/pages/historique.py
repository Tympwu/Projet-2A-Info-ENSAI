"""
Page Streamlit « Historique » : audits enregistrés de l'utilisateur connecté.

Endpoints utilisés :
    GET /historic/{id_utilisateur}
    DELETE /historic/{id_utilisateur}
"""

import streamlit as st

from utils.affichage import afficher_audit, configurer_page
from utils.api_client import api_client
from utils.auth import exiger_connexion
from utils.log_init import get_page_logger

configurer_page(layout="centered")
logger = get_page_logger("home")
utilisateur = exiger_connexion()
id_utilisateur = utilisateur["id"]

st.title("Mes audits")

if st.session_state.pop("historique_supprime", False):
    st.success("Votre historique a été supprimé.")

reponse = api_client.get(f"/historic/{utilisateur['id']}")
if not reponse or reponse["status_code"] != 200:
    st.error("Impossible de charger l'historique.")
    st.stop()

audits = reponse["data"].get("audits", [])
if not audits:
    st.info("Vous n'avez pas encore d'audit enregistré.")
    st.stop()

for a in audits:
    with st.expander(f"Audit n°{a['id']} · {a.get('date', '')} · {a.get('statut', '')}"):
        afficher_audit(a, cle=f"audit_{a['id']}")

st.divider()

with st.expander("Supprimer mon historique"):
    st.write("Supprime tous vos audits enregistrés. Votre compte est conservé.")

    confirmer_historique = st.checkbox(
        "Je confirme vouloir supprimer tout mon historique", key="confirmer_historique"
    )
    if st.button("Supprimer mon historique", disabled=not confirmer_historique):
        suppression = api_client.delete(f"/historic/{id_utilisateur}")
        if suppression and suppression["status_code"] == 200:
            logger.info("Historique supprimé")
            st.session_state["historique_supprime"] = True
            st.rerun()
        else:
            code = suppression["status_code"] if suppression else "aucune réponse"
            logger.error(f"Échec de la suppression de l'historique : {code}")
            st.error(f"La suppression a échoué (code {code}).")   # test
