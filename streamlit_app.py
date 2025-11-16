import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import extract_all_over_under_lines, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="DEBUG - Toate Liniile Over/Under",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 DEBUG - Toate Liniile Over/Under")
st.write("Testează derularea pentru a încărca TOATE liniile")

# Forțează headless
HEADLESS = True

# Input URL (cu home-away)
match_url = st.text_input(
    "🔗 URL cu Home/Away",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de test
if st.button("🚀 Extrage TOATE Liniile (cu derulare)"):
    if match_url:
        # Instalează Playwright
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        # Rulează testul
        with st.spinner("Se derulează și se extrag toate liniile... (poate dura 30 de secunde)"):
            results = extract_all_over_under_lines(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ SUCCES! {len(results)} linii găsite")
            
            # Afișează toate liniile
            st.subheader(f"📋 Toate cele {len(results)} linii găsite:")
            
            # Creează DataFrame pentru afișare mai ordonată
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Afișează și primele/ultimele linii pentru verificare
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Primele 5 linii:**")
                for i in range(min(5, len(results))):
                    st.write(f"{i+1}. {results[i]['line']}")
            
            with col2:
                st.write("**Ultimele 5 linii:**")
                for i in range(max(0, len(results)-5), len(results)):
                    st.write(f"{i+1}. {results[i]['line']}")
            
        else:
            st.error("❌ EȘEC - Nu s-au găsit linii")
            
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("**Îmbunătățire:** Acum codul derulează pentru a încărca toate liniile (lazy loading)")
