import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import test_sageti_si_betano, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="TEST - Săgeți și Betano",
    page_icon="🔍", 
    layout="wide"
)

st.title("🔍 TEST - Săgeți și Căutare Betano")
st.write("Verifică dacă săgețile funcționează și dacă găsește Betano în liniile deschise")

# Forțează headless
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL cu Home/Away",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de test
if st.button("🚀 Testează Săgeți și Betano"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se testează săgețile și căutarea Betano... (poate dura 30 de secunde)"):
            results = test_sageti_si_betano(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ TEST COMPLET! {len(results)} linii testate")
            
            # Afișează rezultatele
            st.subheader("📊 Rezultate Test:")
            
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Statistici
            betano_gasit = sum(1 for r in results if 'DA' in str(r['betano']))
            st.info(f"**Betano găsit în:** {betano_gasit} din {len(results)} linii testate")
            
            if betano_gasit > 0:
                st.success("🎉 Betano a fost găsit! Putem continua cu extracția completă.")
            else:
                st.error("❌ Betano nu a fost găsit. Trebuie să ajustăm selectori.")
                
        else:
            st.error("❌ TEST EȘUAT")
            
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("""
**Ce testează acest cod:**
1. Dă click pe săgețile primelor 3 linii
2. Caută Betano în liniile deschise  
3. Încearcă să extragă cotele de la Betano
4. Afișează rezultatele pentru fiecare linie
""")
