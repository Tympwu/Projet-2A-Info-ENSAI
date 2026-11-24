"""Outils d'authentification pour les pages Streamlit."""

import time

import streamlit as st

PAGE_CONNEXION = "pages/home.py"  # même chemin que celui utilisé dans creer_compte.py


def exiger_connexion() -> dict:
    """À appeler en haut de chaque page protégée.

    Si aucun utilisateur n'est connecté, renvoie vers la page de connexion
    et arrête l'exécution de la page.

    Returns:
        dict: L'utilisateur connecté, tel que stocké à la connexion.
    """
    if "utilisateur" not in st.session_state:
        st.warning("Veuillez vous connecter.")
        time.sleep(1)
        st.switch_page(PAGE_CONNEXION)
        st.stop()
    return st.session_state["utilisateur"]


def deconnecter() -> None:
    """Vide la session et renvoie vers la page de connexion."""
    st.session_state.clear()
    st.switch_page(PAGE_CONNEXION)
