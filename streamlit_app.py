import streamlit as st
import os
from scraper_logic import click_over_under_and_get_url

# Configurare pagină
st.set_page_config(
    page_title="Test Over/Under Navigation",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Test Navigare Over/Under")

# Input URL
match_url = st.text_input(
    "🔗 URL meci (fără over-under)",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Testează Navigarea"):
    if match_url:
        with st.spinner("Se navighează la Over/Under..."):
            result_url = click_over_under_and_get_url(match_url, headless=False)
        
        if result_url:
            st.success("✅ Navigare reușită!")
            st.info(f"**URL Over/Under:** {result_url}")
        else:
            st.error("❌ Navigarea a eșuat")
    else:
        st.warning("⚠️ Introdu un URL")
