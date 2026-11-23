import json

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.auth import exiger_connexion

exiger_connexion()
audit_id = st.session_state.get("audit_id")
if audit_id is None:
    st.info("Aucun audit sélectionné.")
    st.stop()

reponse = api_client.get(f"/audit/{audit_id}")
if not reponse or reponse["status_code"] != 200:
    st.error(f"Audit indisponible (code {reponse['status_code'] if reponse else 'aucune réponse'}).")
    st.stop()
audit = reponse["data"]

st.title(f"Audit n°{audit['id']}")

if audit["statut"] == "validé":
    st.success("Audit validé ✅")
elif audit["statut"] == "refusé":
    st.error("Audit refusé ❌")
else:
    st.warning(f"Statut : {audit['statut']}")


def formater(valeur, format_="{:.2f}", defaut="—"):
    """Formate une valeur numérique, ou renvoie un tiret si elle est absente."""
    return format_.format(valeur) if valeur is not None else defaut


col1, col2, col3 = st.columns(3)
col1.metric("Score", formater(audit.get("score"), "{:.1f}"))
col2.metric("Émissions de CO₂", formater(audit.get("emissionCO2_total")))
col3.metric("Complexité max", audit.get("complexite_max") or "—")

st.subheader("Détail par fichier")
fichiers = audit.get("dossier", {}).get("liste_fichiers", [])
if fichiers:
    st.dataframe(pd.DataFrame(fichiers), use_container_width=True)
else:
    st.info("Aucun fichier dans ce dossier.")

st.subheader("Certificat et SBOM")


def telecharger_json(titre: str, chemin: str, nom_fichier: str, bouton: str):
    """Récupère un JSON via l'API et le propose en téléchargement."""
    reponse = api_client.get(chemin)
    if reponse["status_code"] != 200:
        st.error(f"{titre} indisponible (code {reponse['status_code']}).")
        return None
    st.download_button(
        bouton,
        data=json.dumps(reponse["data"], ensure_ascii=False, indent=2),
        file_name=nom_fichier,
        mime="application/json",
    )
    return reponse["data"]


# --- Certificat : affichage + téléchargement ---
rep_certif = api_client.get(f"/audit/{audit_id}/certificat")
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

    st.download_button(
        "📄 Télécharger le certificat (JSON)",
        data=json.dumps(certificat, ensure_ascii=False, indent=2),
        file_name=f"certificat_audit_{audit_id}.json",
        mime="application/json",
    )
else:
    st.error(f"Certificat indisponible (code {rep_certif['status_code']}).")

# --- SBOM : téléchargement ---
telecharger_json(
    "SBOM",
    f"/audit/{audit_id}/sbom",
    f"sbom_audit_{audit_id}.json",
    "📦 Télécharger le SBOM (CycloneDX)",
)
