import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

st.set_page_config(page_title="Analyse CO₂", page_icon="🌱")
logger = get_page_logger("analyse_CO2")

audit_id = st.session_state.get("audit_id")
if audit_id is None:
    st.info("Aucun audit sélectionné. Lancez d'abord un audit.")
    if st.button("Nouvel audit"):
        st.switch_page("pages/nouvel_audit.py")
    st.stop()

st.title(f"Analyse CO₂ de l'audit n°{audit_id}")
st.write("Estimation des émissions de CO₂ liées à l'exécution de votre code.")

n = st.number_input("Taille de l'entrée de référence (n)", min_value=1, value=500, step=100)

if st.button("Lancer l'analyse", type="primary"):
    with st.spinner("Calcul en cours..."):
        reponse = api_client.post(
            f"/audit/detail_audit?id_audit={audit_id}&taille_entree={int(n)}",
            timeout=60,
        )
    if reponse and reponse["status_code"] == 200:
        st.session_state["emissions"] = reponse["data"]
    else:
        code = reponse["status_code"] if reponse else "aucune réponse"
        logger.error(f"Échec de l'analyse CO2 : {code}")
        st.error(f"L'analyse a échoué (code {code}).")

emissions = st.session_state.get("emissions")
if emissions and emissions["id"] == audit_id:
    st.divider()
    st.metric("Émissions de CO₂ totales", f"{(emissions['emissionCO2_total'] or 0):.2f}")
    st.subheader("Détail par fichier")
    st.dataframe(pd.DataFrame(emissions["dossier"]["liste_fichiers"]), use_container_width=True)

st.divider()
if st.button("Retour au nouvel audit"):
    st.switch_page("pages/nouvel_audit.py")
