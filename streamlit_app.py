import streamlit as st
import pandas as pd
import time
import sys
import subprocess
import os
from scraper_logic import extract_all_over_under_lines, install_playwright

# Configurare pagină Streamlit
st.set_page_config(
    page_title="Extractor Cote Over/Under Betano",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 Extractor Cote Over/Under Betano")
st.write("Extrage toate cotele de closing de la Betano pentru toate liniile Over/Under")

# Forțează headless pe orice mediu server
HEADLESS = True

# Input URL
match_url = st.text_input(
    "🔗 URL Over/Under",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#over-under;1"
)

# Buton de extracție
if st.button("🚀 Extrage Toate Cotele Betano"):
    if match_url and "#over-under" in match_url:
        # Instalează Playwright dacă e necesar
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        # Rulează extracția
        with st.spinner("Se extrag toate liniile Over/Under... (poate dura 1-2 minute)"):
            results = extract_all_over_under_lines(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ Extracție finalizată! {len(results)} linii găsite")
            
            # Creează DataFrame
            df = pd.DataFrame(results)
            
            # Afișează tabel
            st.subheader("📊 Toate Cotele Betano - Over/Under")
            st.dataframe(
                df.style.format({
                    'over': '{:.2f}',
                    'under': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Statistici
            st.subheader("📈 Statistici")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Linii", len(results))
            
            with col2:
                avg_over = df['over'].mean()
                st.metric("Over Mediu", f"{avg_over:.2f}")
            
            with col3:
                avg_under = df['under'].mean()
                st.metric("Under Mediu", f"{avg_under:.2f}")
            
            # Export CSV
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descarcă CSV",
                csv,
                "betano_all_odds.csv",
                "text/csv",
                use_container_width=True
            )
            
        else:
            st.error("❌ Nu s-au putut extrage datele Betano")
            st.info("""
            **Posibile cauze:**
            - Betano nu are cote pentru acest meci
            - Structura paginii s-a schimbat
            - Conexiune lentă sau timeout
            """)
    else:
        st.warning("⚠️ URL-ul trebuie să conțină #over-under")

# Informații
with st.expander("ℹ️ Cum funcționează"):
    st.markdown("""
    1. App-ul navighează la pagina Over/Under
    2. Găsește toate liniile disponibile (ex: +201.5, +202.5, etc.)
    3. Dă click pe săgeata fiecărei linii pentru a o deschide
    4. Caută Betano în lista de bookmakers
    5. Extrage cotele de closing (Over și Under)
    6. Afișează toate datele într-un tabel
    """)

st.write("---")
st.write("**Notă:** Procesul poate dura 1-2 minute pentru a extrage toate liniile")
