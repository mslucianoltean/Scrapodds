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

st.title("🏀 Extractor Cote Betano (Primul Bookmaker)")
st.write("Extrage cotele de la PRIMUL bookmaker (Betano) pentru toate liniile Over/Under")

# Forțează headless
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL meci (cu Over/Under)",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#over-under;1"
)

# Buton de extracție
if st.button("🚀 Extrage Cote Betano"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se extrag toate cotele... (poate dura 1-2 minute)"):
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
            
            # Statistici
            st.subheader("📈 Statistici")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Linii cu Cote", len(results))
            
            with col2:
                avg_over = df['over_closing'].mean()
                st.metric("Over Mediu", f"{avg_over:.2f}")
            
            with col3:
                avg_under = df['under_closing'].mean()
                st.metric("Under Mediu", f"{avg_under:.2f}")
            
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
**Acum extragem:**
- ✅ **Întotdeauna primele cote** din primul rând expandat
- ✅ **Betano este primul** bookmaker în listă
- ✅ **Cotele corecte** (1.14, 5.10 etc.)
- ✅ **Pentru toate liniile** Over/Under
""")
