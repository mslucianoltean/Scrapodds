# app.py (COD PRESUPUS PENTRU INTERFAȚA STREAMLIT)

import streamlit as st
import pandas as pd
# Asigură-te că fișierul scraper_logic.py se află în același director
from scraper_logic import scrape_basketball_match_full_data_filtered 
import json

# --- Configurare pagină Streamlit ---
st.set_page_config(page_title="Scraper COTE Baschet", layout="wide")

st.title("🏀 Scraper Linii Baschet (Betano)")
st.caption("Introduceți link-urile pentru Over/Under și Asian Handicap pentru a extrage cotele.")

# --- Formular de Intrare ---
with st.form(key='scrape_form'):
    ou_link = st.text_input(
        "Link Over/Under (O/U)",
        placeholder="Introduceți link-ul Over/Under aici...",
        key="ou_link_input"
    )
    ah_link = st.text_input(
        "Link Asian Handicap (A/H)",
        placeholder="Introduceți link-ul Asian Handicap aici...",
        key="ah_link_input"
    )
    
    submit_button = st.form_submit_button(label='🚀 Începe Scraping-ul')

# --- Logica de Rulare ---
if submit_button:
    if not ou_link or not ah_link:
        st.error("Vă rugăm să introduceți ambele link-uri înainte de a începe.")
    else:
        st.info("Scraping în curs... Vă rugăm să așteptați. Acest proces poate dura până la 30 de secunde.")
        
        # Apelarea funcției de scraping
        with st.spinner('Așteptare răspuns de la Selenium...'):
            try:
                # Funcția este importată din scraper_logic.py
                results = scrape_basketball_match_full_data_filtered(ou_link, ah_link)
                
                # Afișare rezultate
                if 'Error' in results or 'Error_AH' in results or 'Runtime_Error' in results:
                    st.error("❌ EROARE CRITICĂ ÎN TIMPUL SCRAPING-ULUI:")
                    st.json(results)
                else:
                    st.success("✅ Extracție finalizată cu succes!")
                    
                    # --- Afișare Over/Under ---
                    if results.get('Over_Under_Lines'):
                        st.subheader("Over/Under Cotes")
                        ou_df = pd.DataFrame(results['Over_Under_Lines'])
                        st.dataframe(ou_df, use_container_width=True)
                    else:
                        st.warning("Nu au fost găsite linii Over/Under.")
                        st.json(results.get('Error'))

                    # --- Afișare Asian Handicap ---
                    if results.get('Handicap_Lines'):
                        st.subheader("Asian Handicap Cotes")
                        ah_df = pd.DataFrame(results['Handicap_Lines'])
                        st.dataframe(ah_df, use_container_width=True)
                    else:
                        st.warning("Nu au fost găsite linii Asian Handicap.")
                        st.json(results.get('Error_AH'))
                        
            except Exception as e:
                st.error(f"Eroare neașteptată la rularea scriptului principal: {e}")

st.markdown("---")
st.markdown("Asigurați-vă că fișierul `scraper_logic.py` (V20.0) se află alături de `app.py`.")
