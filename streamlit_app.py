import streamlit as st
import pandas as pd
from scraper_logic import extract_betano_complete, install_playwright

st.set_page_config(page_title="Betano Complete", page_icon="🏀")
st.title("🏀 Betano - Proces Complet")
st.write("Home/Away → Over/Under → Săgeată → Betano")

HEADLESS = True

match_url = st.text_input(
    "🔗 URL cu Home/Away", 
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Rulează"):
    if match_url:
        with st.spinner("Se execută..."):
            install_playwright()
            results = extract_betano_complete(match_url, headless=HEADLESS)
        
        if results:
            st.success("✅ SUCCES!")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ Betano negăsit")
    else:
        st.warning("⚠️ Introdu URL")
