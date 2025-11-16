import streamlit as st
import pandas as pd
from scraper_logic import scrape_over_under_data, install_playwright

st.set_page_config(page_title="Over/Under Scraper", page_icon="🔍")
st.title("🔍 Over/Under Scraper")

match_url = st.text_input(
    "🔗 URL meci",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Extrage Datele Betano"):
    if match_url:
        with st.spinner("Se extrag datele Betano..."):
            install_playwright()
            result = scrape_over_under_data(match_url, headless=True)
        
        if result and result['date']:
            st.success(f"✅ {result['numar_bookmakeri']} linii Betano extrase!")
            df = pd.DataFrame(result['date'])
            st.dataframe(df, width='stretch')
        else:
            st.error("❌ Nu s-au putut extrage datele Betano")
    else:
        st.warning("⚠️ Introdu un URL")
