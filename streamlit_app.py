import streamlit as st
import pandas as pd
from scraper_logic import extract_betano_with_link, install_playwright

st.set_page_config(page_title="Betano - Cu Link", page_icon="🏀")
st.title("🏀 Betano - Căutare după LINK")
st.write("**Home/Away → Over/Under → Săgeată → Betano (după LINK) → Cote**")

HEADLESS = True

match_url = st.text_input(
    "🔗 URL cu Home/Away", 
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Rulează cu Link Betano"):
    if match_url:
        with st.spinner("Se execută cu căutare după LINK..."):
            install_playwright()
            results = extract_betano_with_link(match_url, headless=HEADLESS)
        
        if results:
            st.success("✅ BETANO GĂSIT după LINK!")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ Betano negăsit după LINK")
    else:
        st.warning("⚠️ Introdu URL cu Home/Away")
