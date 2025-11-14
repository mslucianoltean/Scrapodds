# app.py

import streamlit as st
import pandas as pd
import json
import os
from scraper_logic import scrape_basketball_match_full_data_filtered, TARGET_BOOKMAKER

st.set_page_config(page_title="OddsPortal Betano Scraper", layout="wide")

st.title("🏀 OddsPortal Scraper Headless")

st.info(
    f"Acest instrument extrage toate liniile (Total și Handicap) de la **{TARGET_BOOKMAKER}** "
    f"pentru orice meci de baschet de pe OddsPortal, incluzând cotele de deschidere și închidere."
)

# 1. Input-ul utilizatorului
match_link = st.text_input(
    "🔗 Introduceți Link-ul OddsPortal:",
    "https://www.oddsportal.com/basketball/usa/nba/phoenix-suns-indiana-pacers-KtP8YyZj/#home-away;1"
)

# 2. Butonul de execuție
if st.button("🚀 Extrage Cotele"):
    if not match_link or "oddsportal.com" not in match_link:
        st.error("Vă rugăm să introduceți un link OddsPortal valid.")
    else:
        # Folosim st.spinner pentru a arăta că aplicația lucrează (Selenium durează)
        with st.spinner("Se extrag datele folosind Chromium Headless... Acest lucru poate dura 10-20 de secunde."):
            
            # 3. Execută funcția de scraping
            results = scrape_basketball_match_full_data_filtered(match_link)
            
            # 4. Afișează rezultatele
            
            # Verifică erorile critice (inițializare driver, etc.)
            if 'Error' in results or 'Runtime_Error' in results:
                st.error("❌ A apărut o eroare critică la execuție.")
                st.json(results)
            else:
                st.success(f"✅ Extragere reușită pentru: **{results.get('Match', 'N/A')}**")
                
                # Afișează datele de bază
                col1, col2, col3 = st.columns(3)
                col1.metric("Meci", results.get('Match', 'N/A'))
                col2.metric("Data", results.get('Date', 'N/A'))
                col3.metric("Scor Final", results.get('Final_Score', 'N/A'))

                st.markdown("---")
                
                # Afișează tabelele de cote
                
                # Over/Under
                st.subheader("📊 Total (Over/Under) Linii")
                if results['Over_Under_Lines']:
                    df_ou = pd.DataFrame(results['Over_Under_Lines'])
                    st.dataframe(df_ou, use_container_width=True)
                else:
                    st.warning("Nicio linie Over/Under găsită de la Betano. Asigurați-vă că meciul a avut cote Betano.")
                    
                # Handicap
                st.subheader("🤝 Handicap (Asian Handicap) Linii")
                if results['Handicap_Lines']:
                    df_h = pd.DataFrame(results['Handicap_Lines'])
                    st.dataframe(df_h, use_container_width=True)
                else:
                    st.warning("Nicio linie Handicap găsită de la Betano. Asigurați-vă că meciul a avut cote Betano.")

                st.markdown("---")
                st.subheader("Output JSON Brut (Pentru Export)")
                st.json(results)
