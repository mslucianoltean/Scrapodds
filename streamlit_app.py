import streamlit as st
import pandas as pd
import json
from scraper_logic import scrape_basketball_match_full_data_filtered # Importăm funcția de scraping

# ----------------------------------------------------------------------
# ⚙️ CONFIGURARE PAGINĂ
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="OddsPortal Scraper",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# 💾 CACHING
# ----------------------------------------------------------------------
# Folosim caching pentru a ne asigura că funcția de scraping rulează
# o singură dată pentru aceeași pereche de link-uri.
@st.cache_data(show_spinner="Rulez scraping-ul... Vă rog să așteptați (poate dura până la 30 de secunde)...")
def run_scraper(ou_url, ah_url):
    """Rulează funcția de scraping și returnează rezultatele."""
    # Apelul funcției cu cele două link-uri necesare
    return scrape_basketball_match_full_data_filtered(ou_url, ah_url)

# ----------------------------------------------------------------------
# 🖥️ INTERFAȚA STREAMLIT
# ----------------------------------------------------------------------

st.title("🏀 OddsPortal Basketball Line Scraper (Betano)")
st.markdown("---")

st.header("URL-uri Meci (Over/Under & Asian Handicap)")

# Input-uri pentru cele două URL-uri
ou_link = st.text_input(
    "URL Over/Under (Total) Meci:",
    placeholder="Ex: https://www.oddsportal.com/basketball/usa/nba/meci-a-meci-b-KtP8YyZj/#over-under;1"
)

ah_link = st.text_input(
    "URL Asian Handicap Meci:",
    placeholder="Ex: https://www.oddsportal.com/basketball/usa/nba/meci-a-meci-b-KtP8YyZj/#ah;1"
)

# Buton de start
if st.button("Start Scraping", type="primary"):
    if ou_link and ah_link:
        
        # 1. Rulare Scraping
        try:
            results = run_scraper(ou_link, ah_link)
        except Exception as e:
            st.error(f"Eroare neașteptată la rularea funcției de scraping: {e}")
            results = None

        if results:
            st.markdown("---")
            st.header(f"Rezultate pentru: **{results.get('Match', 'N/A')}**")
            
            # 2. Verifică erorile de runtime/inițializare
            if 'Error' in results or 'Runtime_Error' in results:
                st.error("❌ EROARE CRITICĂ:")
                st.json(results)
            
            # 3. Afisare Over/Under Lines
            ou_lines = results.get('Over_Under_Lines')
            if ou_lines:
                st.subheader("📊 Linii Over/Under (Betano)")
                df_ou = pd.DataFrame(ou_lines)
                st.dataframe(df_ou, use_container_width=True)
            elif 'Error_Over_Under' in results:
                st.warning(f"⚠️ Eroare la OU: {results['Error_Over_Under']}")

            st.markdown("---")

            # 4. Afisare Handicap Lines
            handicap_lines = results.get('Handicap_Lines')
            if handicap_lines:
                st.subheader("📈 Linii Asian Handicap (Betano)")
                df_ah = pd.DataFrame(handicap_lines)
                st.dataframe(df_ah, use_container_width=True)
            elif 'Error_Handicap' in results:
                st.warning(f"⚠️ Eroare la Handicap: {results['Error_Handicap']}")

            # 5. Afisare JSON brut (pentru debug)
            with st.expander("Vizualizare JSON Brut"):
                st.json(results)

    else:
        st.warning("Vă rog să introduceți ambele URL-uri pentru a continua.")

st.markdown("---")
st.caption("Asigurați-vă că fișierul `scraper_logic.py` este la zi cu cele mai recente modificări.")
