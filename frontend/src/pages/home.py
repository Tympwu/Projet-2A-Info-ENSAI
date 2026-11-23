"""
Page d'accueil Streamlit.

Permet de se connecter, de créer un compte ou de réinitialiser la base de données.

Endpoints utilisés :
    POST /user/login
    DELETE /user/{id_utilisateur}
    GET /reset_database
"""

import streamlit as st
from streamlit import config

from utils.affichage import configurer_page
from utils.api_client import api_client
from utils.log_init import get_page_logger

PAGE_APRES_CONNEXION = "pages/nouvel_audit.py"
PAGE_CREATION_COMPTE = "pages/creer_compte.py"
ID_admin = 1

CLES_SESSION_UTILISATEUR = ("utilisateur", "dernier_audit", "audit_id")

configurer_page(layout="centered")  # remplace ton st.set_page_config(...)
logger = get_page_logger("home")


def vider_session_utilisateur() -> None:
    """Retire de la session les informations de l'utilisateur connecté."""
    for cle in CLES_SESSION_UTILISATEUR:
        st.session_state.pop(cle, None)


st.markdown(
    f"""
    <div style="text-align:center">
        <h1 style="color:{config.get_option("theme.primaryColor")}">Audit de code</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

utilisateur = st.session_state.get("utilisateur")
if utilisateur:
    is_admin = ID_admin == utilisateur["id"]
    st.write(f"Connecté en tant que **{utilisateur.get('name', '')}**.")

    col1, col2 = st.columns(2)
    if col1.button("Nouvel audit", type="primary"):
        st.switch_page(PAGE_APRES_CONNEXION)
    if col2.button("Se déconnecter"):
        logger.info(f"Déconnexion de l'utilisateur {utilisateur.get('name', '')}")
        for cle in CLES_SESSION_UTILISATEUR:
            st.session_state.pop(cle, None)
        st.rerun()
    if not is_admin:
        with st.expander("Supprimer mon compte"):
            st.warning("Action définitive : votre compte et vos données seront supprimés.")

            mot_de_passe = st.text_input("Mot de passe", type="password", key="mdp_suppression")
            confirmer = st.checkbox(
                "Je confirme vouloir supprimer définitivement mon compte",
                key="confirmer_suppression",
            )

            if st.button(
                "Supprimer définitivement mon compte",
                disabled=not (mot_de_passe and confirmer),
            ):
                # On revérifie le mot de passe pour éviter une suppression par erreur
                verification = api_client.post(
                    "/user/login",
                    json={"name": utilisateur["name"], "mot_de_passe": mot_de_passe},
                )
                if not verification or verification["status_code"] != 200:
                    st.error("Mot de passe incorrect.")
                    st.stop()

                reponse = api_client.delete(f"/user/{utilisateur['id']}")
                if reponse and reponse["status_code"] == 200:
                    logger.info(f"Compte de {utilisateur.get('name', '')} supprimé")
                    vider_session_utilisateur()
                    st.session_state["compte_supprime"] = True
                    st.rerun()
                else:
                    code = reponse["status_code"] if reponse else "aucune réponse"
                    logger.error(f"Échec de la suppression du compte : {code}")
                    st.error(f"La suppression a échoué (code {code}).")

    if is_admin:
        if st.button("Réinitialiser la base de données", type="primary"):
            logger.info("Réinitialisation de la base de données")
            response = api_client.get("/reset_database")

            if response and response["status_code"] == 200:
                logger.info("Base de données réinitialisée")
                st.toast("Base de données réinitialisée ✅")
            else:
                logger.error("Échec de la réinitialisation de la base")
                st.toast("Échec de la réinitialisation ❌")

    st.stop()
if st.session_state.pop("compte_supprime", False):
    st.success("Votre compte a été supprimé.")

username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")

with st.container(horizontal_alignment="center"):
    if st.button("Se connecter", disabled=not username or not password, shortcut="Enter"):
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
