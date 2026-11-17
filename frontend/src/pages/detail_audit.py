import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth import exiger_connexion

exiger_connexion()
audit_id = st.session_state.get("audit_id")
if audit_id is None:
    st.info("Aucun audit sélectionné.")
    st.stop()

reponse = api_client.get(f"/audits/{audit_id}")
audit = reponse["data"]

st.title(f"Audit n°{audit['id']}")

if audit["statut"] == "validé":
    st.success("Audit validé ✅")
elif audit["statut"] == "refusé":
    st.error("Audit refusé ❌")
else:
    st.warning(f"Statut : {audit['statut']}")

col1, col2, col3 = st.columns(3)
col1.metric("Score", f"{audit['score']:.1f}")
col2.metric("Émissions de CO₂", f"{audit['emissionCO2_total']:.2f}")
col3.metric("Complexité max", audit["complexite_max"])

st.subheader("Détail par fichier")
st.dataframe(pd.DataFrame(audit["fichiers"]), use_container_width=True)
