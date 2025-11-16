import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import extract_first_bookmaker_odds, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="Extractor Cote Betano", 
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 Extractor Cote Betano (Cu Click Forțat)")
st.write("Dă click FORȚAT pe Over/Under pentru a încărca datele, apoi extrage cotele")

# Forțează headless
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL meci (orice tab)",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de extracție
if st.button("🚀 Extrage Cote Betano"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se dă click pe Over/Under și se extrag cotele... (poate dura 30 secunde)"):
            results = extract_first_bookmaker_odds(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ EXTRACȚIE REUȘITĂ! {len(results)} linii cu cote Betano")
            
            # Afișează rezultatele
            st.subheader("📊 Cote Betano - Closing")
            
            df = pd.DataFrame(results)
            st.dataframe(
                df.style.format({
                    'over_closing': '{:.2f}',
                    'under_closing': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descarcă CSV",
                csv,
                "betano_odds.csv",
                "text/csv",
                use_container_width=True
            )
            
        else:
            st.error("❌ Nu s-au găsit cote pentru nicio linie")
            st.info("Verifică consola pentru detalii de debug")
            
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("""
**Îmbunătățiri:**
- ✅ **Click FORȚAT pe Over/Under** indiferent de URL-ul curent
- ✅ **Verifică dacă Over/Under e deja activ**
- ✅ **Debug extins** pentru a vedea ce se întâmplă
- ✅ **Testează doar primele 5 linii** pentru rapiditate
- ✅ **Verifică numărul de rânduri expandate**
""")
