"""
Page Streamlit de création de compte utilisateur.

Permet de créer un compte avec un nom d'utilisateur, un email et un mot de passe.

Endpoint utilisé :
    POST /user/
"""


import streamlit as st

from utils.affichage import configurer_page
from utils.api_client import api_client
from utils.log_init import get_page_logger

configurer_page(layout="centered")

st.title("Créer un compte")
logger = get_page_logger("creer_compte")

username = st.text_input("Nom d'utilisateur", max_chars=30)
email = st.text_input("Email")
password = st.text_input("Mot de passe", type="password")
password_confirmation = st.text_input("Confirmer le mot de passe", type="password")

mdp_assez_long = len(password) >= 8
mdp_identiques = bool(password) and password == password_confirmation

st.write("✅" if mdp_assez_long else "❌", "Au moins 8 caractères")
st.write("✅" if mdp_identiques else "❌", "Les deux mots de passe sont identiques")

formulaire_valide = bool(username) and mdp_assez_long and mdp_identiques

with st.container(horizontal_alignment="center"):
    if st.button("Créer le compte", width=200, disabled=not formulaire_valide):
        logger.info(f"Création d'un compte pour l'utilisateur : {username}")
        utilisateur = {
            "name": username,
            "mot_de_passe": password,
            "email": email,
        }

        try:
            response = api_client.post("/user/", json=utilisateur)
        except Exception as e:
            logger.exception(f"Erreur lors de l'appel à l'API : {e}")
            st.error(f"Connexion impossible : {e}")
        else:
            if not response:
                logger.error("Réponse vide de l'API")
                st.error("Pas de réponse du serveur.")
            elif response["status_code"] in (200, 201):
                logger.info("Compte créé avec succès")
                st.success(f"Compte {username} créé avec succès ! 🎉 Vous pouvez vous connecter.")
            else:
                logger.warning(f"Échec de la création : status {response['status_code']}")
                st.error(f"Échec (code {response['status_code']}).")
                detail = (
                    response["data"].get("detail") if isinstance(response["data"], dict) else None
                )
                if isinstance(detail, str):
                    st.caption(detail)

if st.button("Retour à l'accueil", type="primary"):
    st.switch_page("pages/home.py")
