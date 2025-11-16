import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import extract_all_over_under_lines, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="DEBUG - Extractor Linii Over/Under",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 DEBUG - Verificare Linii Over/Under")
st.write("Testează dacă se încarcă corect liniile după click pe Over/Under")

# Forțează headless
HEADLESS = True

# Input URL (cu home-away)
match_url = st.text_input(
    "🔗 URL cu Home/Away",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de test
if st.button("🚀 Testează Încărcarea Liniilor"):
    if match_url:
        # Instalează Playwright
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        # Rulează testul
        with st.spinner("Se testează încărcarea liniilor..."):
            results = extract_all_over_under_lines(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ TEST REUȘIT! {len(results)} linii găsite")
            
            # Afișează liniile găsite
            st.subheader("📋 Liniile găsite:")
            for i, line in enumerate(results):
                st.write(f"{i+1}. {line['line']}")
            
            st.info("""
            **Următorul pas:** 
            Dacă liniile sunt găsite, putem continua cu click pe săgeți și căutarea Betano.
            """)
            
        else:
            st.error("❌ TEST EȘUAT - Nu s-au găsit linii")
            st.info("""
            **Debug necesar:**
            - Verifică dacă se dă click corect pe Over/Under
            - Verifică dacă liniile se încarcă în browser
            - Verifică consola pentru mesaje de eroare
            """)
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("**Scop:** Verifică dacă după click pe Over/Under se încarcă liniile cu săgeți")
