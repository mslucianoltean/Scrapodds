import streamlit as st
import time
import sys
import subprocess
import os
from scraper_logic import click_over_under_and_get_url, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="Test Over/Under Navigation",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Test Navigare Over/Under")
st.write("Acest app testează dacă Playwright poate da click pe tab-ul Over/Under")

# Forțează headless pe orice mediu server
HEADLESS = True  # FORȚAT headless

# Input URL
match_url = st.text_input(
    "🔗 URL meci (fără over-under)",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de test
if st.button("🚀 Testează Navigarea"):
    if match_url:
        # Instalează Playwright dacă e necesar
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        # Rulează testul cu headless FORȚAT
        with st.spinner("Se navighează la Over/Under... (poate dura 10-15 secunde)"):
            result_url = click_over_under_and_get_url(match_url, headless=HEADLESS)
        
        if result_url:
            st.success("✅ Navigare reușită!")
            st.info(f"**URL Over/Under:** {result_url}")
            
            # Afișează diferența dintre URL-uri
            st.subheader("🔍 Comparație URL-uri:")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**URL inițial:**")
                st.code(match_url)
            with col2:
                st.write("**URL după click:**")
                st.code(result_url)
        else:
            st.error("❌ Navigarea a eșuat")
            st.info("⚠️ Browser-ul rulează în modul headless (fără interfață vizibilă)")
    else:
        st.warning("⚠️ Introdu un URL")

# Informații suplimentare
with st.expander("ℹ️ Cum funcționează"):
    st.markdown("""
    1. App-ul primește un URL OddsPortal fără `#over-under`
    2. Playwright deschide browser-ul în mod headless (fără interfață vizibilă)
    3. Dă click pe tab-ul Over/Under
    4. Așteaptă 5 secunde pentru încărcare
    5. Capturează noul URL cu `#over-under`
    6. Afișează rezultatul
    """)

st.write("---")
st.write("**Mod headless activat** - Browser-ul rulează în fundal fără interfață vizuală")
