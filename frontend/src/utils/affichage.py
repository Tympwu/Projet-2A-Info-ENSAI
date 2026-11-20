"""Fonctions d'affichage réutilisables entre les pages."""

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

# affichage.py est dans src/utils/ : on remonte d'un cran pour trouver src/assets/
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def afficher_audit(audit: dict, cle: str = "audit") -> None:
    """Affiche le résultat complet d'un audit (statut, métriques, détail par fichier).

    Args:
        audit (dict): Audit renvoyé par l'API.
        cle (str): Préfixe unique pour les widgets, utile si plusieurs audits
            sont affichés sur la même page.
    """
    statut = audit.get("statut")
    if statut == "validé":
        st.success("Audit validé ✅")
    elif statut == "refusé":
        st.error("Audit refusé ❌")
    else:
        st.warning(f"Statut : {statut}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", audit.get("score"))
    col2.metric("Complexité", f"O(n^{audit.get("complexite_total")})")
    col3.metric("Émissions de CO₂ totales", f"{(audit.get('emissionCO2_total') or 0):.2f}g/kWh")

    fichiers = audit.get("dossier")["liste_fichiers"]
    if fichiers:
        st.subheader("Détail par fichier")
        st.dataframe(pd.DataFrame(fichiers), width="stretch")

    certificat = audit.get("certificat_pdf")  # PDF encodé en base64, si l'audit est validé
    if statut == "validé" and certificat:
        st.download_button(
            "Télécharger le certificat (PDF)",
            data=base64.b64decode(certificat),
            file_name="certificat_audit.pdf",
            mime="application/pdf",
            key=f"{cle}_certificat",
        )


def configurer_page(layout: str = "centered") -> None:
    """Configure la page (titre, icône, mise en page) et affiche le logo CleanOps.

    À appeler en tout premier dans chaque page, avant toute autre commande Streamlit.

    Args:
        layout (str): "centered" ou "wide".
    """
    st.set_page_config(
        page_title="CleanOps",
        page_icon=str(ASSETS / "bouclier.png"),
        layout=layout,
    )
    st.logo(
        str(ASSETS / "logo_cleanops.png"),
        icon_image=str(ASSETS / "bouclier.png"),
        size="large",
    )
