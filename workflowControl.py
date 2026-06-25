import streamlit as st
import streamlit.components.v1 as components

# Configuration de la page Streamlit pour qu'elle prenne tout l'écran
st.set_page_config(layout="wide", page_title="Studio Workflow Control")

# Lire le contenu de ton fichier HTML
with open("index.html", "r", encoding="utf-8") as f:
    html_code = f.read()

# Injecter le code HTML/JS/CSS dans l'application Streamlit
# On lui donne une grande hauteur (ex: 900px) pour éviter les barres de défilement internes
components.html(html_code, height=900, scrolling=True)