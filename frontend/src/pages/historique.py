"""
Page Streamlit « Historique » : audits enregistrés de l'utilisateur connecté.

Endpoints utilisés :
    GET /historic/{id_utilisateur}
    DELETE /audit/{id_audit}
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

nonce = st.session_state.get("nonce_historique", 0)

st.title("Mes audits")

message = st.session_state.pop("message_historique", None)
if message:
    afficher = st.success if message[0] == "succes" else st.warning
    afficher(message[1])

reponse = api_client.get(f"/historic/{utilisateur['id']}")
if not reponse or reponse["status_code"] != 200:
    st.error("Impossible de charger l'historique.")
    st.stop()

audits = reponse["data"].get("audits", [])
if not audits:
    st.info("Vous n'avez pas encore d'audit enregistré.")
    st.stop()

st.caption("Cochez les audits à supprimer, puis confirmez en bas de page.")

selection = []
for a in audits:
    col_case, col_audit = st.columns([1, 12], vertical_alignment="top")
    if col_case.checkbox(
        f"Sélectionner l'audit {a['id']}",
        key=f"selection_{a['id']}",
        label_visibility="collapsed",
    ):
        selection.append(a["id"])
    with col_audit.expander(f"Audit n°{a['id']} · {a.get('date', '')} · {a.get('statut', '')}"):
        afficher_audit(a, cle=f"audit_{a['id']}")

st.divider()

if selection:
    st.write(f"**{len(selection)}** audit(s) sélectionné(s).")
    confirmer_selection = st.checkbox(
        "Je confirme la suppression des audits sélectionnés",
        key=f"confirmer_selection_{nonce}",
    )
    if st.button("Supprimer la sélection", type="primary", disabled=not confirmer_selection):
        echecs = []
        for id_audit in selection:
            suppression = api_client.delete(f"/audit/{id_audit}")
            if not suppression or suppression["status_code"] != 200:
                echecs.append(id_audit)
                logger.error(f"Échec de la suppression de l'audit {id_audit}")
            else:
                logger.info(f"Audit {id_audit} supprimé")

        nb_supprimes = len(selection) - len(echecs)
        if echecs:
            ids = ", ".join(str(i) for i in echecs)
            st.session_state["message_historique"] = (
                "avertissement",
                f"{nb_supprimes} audit(s) supprimé(s). Échec pour : {ids}.",
            )
        else:
            st.session_state["message_historique"] = (
                "succes",
                f"{nb_supprimes} audit(s) supprimé(s).",
            )
        st.session_state["nonce_historique"] = nonce + 1
        st.rerun()
else:
    st.caption("Aucun audit sélectionné.")


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
