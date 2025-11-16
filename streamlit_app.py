import streamlit as st
from scraper_logic import debug_container_content

st.set_page_config(page_title="DEBUG Container", page_icon="🐛")
st.title("🐛 DEBUG - Conținut Container Expand")
st.write("Afișează EXACT ce este în containerul expandat")

match_url = st.text_input(
    "🔗 URL cu Home/Away", 
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🐛 Rulează DEBUG"):
    if match_url:
        with st.spinner("Se rulează DEBUG..."):
            result = debug_container_content(match_url)
        
        if "status" in result:
            st.success("✅ DEBUG complet! Verifică CONSOLA pentru output")
        else:
            st.error(f"❌ Eroare: {result['error']}")
    else:
        st.warning("⚠️ Introdu URL")
