import streamlit as st
import pandas as pd
from scraper_logic import extract_betano_complete, install_playwright

st.set_page_config(page_title="Betano - Proces Complet", page_icon="🏀")
st.title("🏀 Betano - Proces COMPLET")
st.write("**Home/Away → Click Over/Under → Click săgeată → Betano**")

HEADLESS = True

match_url = st.text_input(
    "🔗 URL cu Home/Away", 
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Rulează Procesul Complet"):
    if match_url:
        with st.spinner("Se execută procesul complet..."):
            install_playwright()
            results = extract_betano_complete(match_url, headless=HEADLESS)
        
        if results:
            st.success("✅ SUCCES! Proces complet executat")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ Betano negăsit în procesul complet")
    else:
        st.warning("⚠️ Introdu URL cu Home/Away")
