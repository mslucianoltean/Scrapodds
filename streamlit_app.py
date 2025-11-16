import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import debug_complete_extraction, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="DEBUG COMPLET - Betano", 
    page_icon="🐛",
    layout="wide"
)

st.title("🐛 DEBUG COMPLET - De ce nu găsește Betano?")
st.write("Verifică totul pas cu pas pentru a identifica problema")

# Forțează headless
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL cu Home/Away",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de debug
if st.button("🐛 Rulează Debug Complet"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se rulează debug complet... (verifică consola)"):
            result = debug_complete_extraction(match_url, headless=HEADLESS)
        
        # Afișează rezumat
        st.subheader("📊 Rezumat Debug")
        
        if "error" in result:
            st.error(f"❌ EROARE: {result['error']}")
        else:
            st.success("✅ Debug completat!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Linii găsite", result['linii_gasite'])
            with col2:
                st.metric("Rânduri expandate", result['randuri_expandate'])
            with col3:
                st.metric("Bookmakeri găsiți", result['bookmakeri_gasiti'])
        
        st.info("""
        **Verifică consola pentru detalii complete despre:**
        - Câți bookmakeri sunt în listă
        - Dacă Betano apare în listă
        - Ce cote au primii bookmakeri
        - Dacă rândurile se expandează corect
        """)
            
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("""
**Acest debug va arăta:**
1. ✅ Dacă se navighează corect
2. ✅ Dacă se dă click pe Over/Under  
3. ✅ Câte linii se găsesc
4. ✅ Dacă săgețile funcționează
5. ✅ Câți bookmakeri sunt în listă
6. ✅ Dacă Betano este în listă
7. ✅ Ce cote au primii bookmakeri
""")
