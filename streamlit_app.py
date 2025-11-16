import streamlit as st
import pandas as pd
from scraper_logic import get_betano_over_under_odds, install_playwright

st.set_page_config(page_title="Over/Under Cote", page_icon="📊")
st.title("📊 Over/Under Cote Betano")

# Input URL
match_url = st.text_input(
    "🔗 URL meci",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Extrage Cotele"):
    if match_url:
        with st.spinner("Se extrag cotele..."):
            install_playwright()
            result = get_betano_over_under_odds(match_url, headless=True)
        
        if result and result['data']:
            st.success(f"✅ {len(result['data'])} linii găsite")
            
            # Afișează tabel simplu
            df = pd.DataFrame(result['data'])
            st.dataframe(df, use_container_width=True)
            
            # Descarcă CSV
            csv = df.to_csv(index=False)
            st.download_button("📥 Descarcă CSV", csv, "cote_over_under.csv")
        else:
            st.error("❌ Nu s-au găsit date")
    else:
        st.warning("⚠️ Introdu URL")
