"""
Page d'accueil Streamlit.

Permet de se connecter, de créer un compte ou de réinitialiser la base de données.

Endpoints utilisés :
    POST /user/login
    GET /reset_database
"""

import streamlit as st
from streamlit import config

from utils.api_client import api_client
from utils.log_init import get_page_logger

PAGE_APRES_CONNEXION = "pages/nouvel_audit.py"
PAGE_CREATION_COMPTE = "pages/creer_compte.py"

st.set_page_config(page_title="Audit de code", page_icon="🌱", layout="centered")

if "utilisateur" in st.session_state:
    st.switch_page(PAGE_APRES_CONNEXION)

st.markdown(
    f"""
    <div style="text-align:center">
        <h1 style="color:{config.get_option("theme.primaryColor")}">Audit de code</h1>
    </div>
    """,
    unsafe_allow_html=True,
)
logger = get_page_logger("home")

username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")

with st.container(horizontal_alignment="center"):
    if st.button("Se connecter", disabled=not username or not password):
        logger.info(f"Tentative de connexion pour l'utilisateur : {username}")

        try:
            response = api_client.post(
                "/user/login",
                json={"name": username, "mot_de_passe": password},
            )

            if response:
                status_code = response.get("status_code")
                data = response.get("data")

                if status_code == 200:
                    logger.info(f"Utilisateur {username} connecté.")
                    st.session_state["utilisateur"] = data
                    st.session_state["access_token"] = data.get("access_token")
                    st.success(f"Bienvenue {data.get('name', username)} ! 🎉")
                    st.switch_page(PAGE_APRES_CONNEXION)
                elif status_code in (401, 404):
                    logger.warning(f"Connexion refusée ({status_code}) pour {username}.")
                    st.error(f"Connexion refusée (code {status_code}).")
                    detail = data.get("detail") if isinstance(data, dict) else None
                    if isinstance(detail, str):
                        st.caption(detail)
                else:
                    logger.error(f"Échec de la connexion : status {status_code}")
                    st.error(f"Erreur serveur (code {status_code}), voir les logs.")
            else:
                logger.error("Réponse vide de l'API")
                st.error("Pas de réponse du serveur.")

        except Exception as e:
            logger.exception(f"Erreur lors de l'appel à l'API : {e}")
            st.error(f"Erreur de connexion : {e}")

st.space("small")

if st.button("Créer un compte"):
    st.switch_page(PAGE_CREATION_COMPTE)

if st.button("Réinitialiser la base de données", type="primary"):
    logger.info("Réinitialisation de la base de données")
    response = api_client.get("/reset_database")

    if response:
        logger.info("Base de données réinitialisée")
        st.toast("Base de données réinitialisée ✅")
    else:
        logger.error("Échec de la réinitialisation de la base")
        st.toast("Échec de la réinitialisation ❌")
