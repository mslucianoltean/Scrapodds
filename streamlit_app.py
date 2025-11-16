import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import extract_betano_closing_odds, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="Extractor Cote Closing Betano", 
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 Extractor Cote CLOSING Betano")
st.write("Extrage toate cotele de CLOSING de la Betano pentru toate liniile Over/Under")

# Forțează headless
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL cu Home/Away",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

# Buton de extracție
if st.button("🚀 Extrage Cote Closing Betano"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se extrag toate cotele de closing... (poate dura 1-2 minute)"):
            results = extract_betano_closing_odds(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ EXTRACȚIE REUȘITĂ! {len(results)} linii cu cote Betano")
            
            # Afișează rezultatele
            st.subheader("📊 Cote CLOSING Betano")
            
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
            st.subheader("📈 Statistici Cote Closing")
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
                "betano_closing_odds.csv",
                "text/csv",
                use_container_width=True
            )
            
        else:
            st.error("❌ Nu s-au găsit cote Betano pentru nicio linie")
            st.info("""
            **Posibile cauze:**
            - Betano nu oferă cote pentru acest meci
            - Structura paginii s-a schimbat
            - Probleme de încărcare
            """)
            
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("""
**Acum extragem corect:**
- ✅ Rândurile expandate cu `data-testid="over-under-expanded-row"`
- ✅ Betano prin `data-testid="outrights-expanded-bookmaker-name"`
- ✅ Cotele de closing cu `.odds-text` (1.14, 5.10 etc.)
""")
