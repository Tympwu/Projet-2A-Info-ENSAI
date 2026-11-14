import streamlit as st

from utils.affichage import afficher_audit
from utils.api_client import api_client
from utils.log_init import get_page_logger

st.set_page_config(page_title="Nouvel audit", page_icon="🌱")
logger = get_page_logger("nouvel_audit")

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

fichiers = st.file_uploader(
    "Fichiers (.py, requirements.txt, pyproject.toml, uv.lock)",
    accept_multiple_files=True,
)

if st.button("Lancer l'audit", type="primary", disabled=not fichiers):
    with st.spinner("Analyse en cours..."):
        files = [
            ("liste_fichier", (f.name, f.getvalue(), f.type or "application/octet-stream"))
            for f in fichiers
        ]
        donnees = {"utilisateur_id": utilisateur["id"]} if utilisateur else None
        reponse = api_client.post(
            "/audit/start_audit",
            files=files,
            data=donnees,
            timeout=60,  # une analyse peut dépasser les 5 s par défaut
        )

    if reponse and reponse["status_code"] == 200:
        st.session_state["dernier_audit"] = reponse["data"]
    else:
        code = reponse["status_code"] if reponse else "aucune réponse"
        logger.error(f"Échec de l'audit : {code}")
        st.error(f"L'audit a échoué (code {code}). {reponse['data'] if reponse else ''}")

audit = st.session_state.get("dernier_audit")
if audit:
    st.divider()
    st.subheader("Résultat de l'audit")
    afficher_audit(audit, cle="nouvel_audit")
    if not utilisateur:
        st.caption("Audit non enregistré : connectez-vous pour conserver vos audits.")
