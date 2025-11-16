import streamlit as st
import pandas as pd
from scraper_logic import scrape_over_under_data, install_playwright

st.set_page_config(page_title="Over/Under Scraper", page_icon="🔍")
st.title("🔍 Over/Under Scraper")

match_url = st.text_input(
    "🔗 URL meci",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Extrage Toți Bookmakerii"):
    if match_url:
        with st.spinner("Se extrag datele..."):
            install_playwright()
            result = scrape_over_under_data(match_url, headless=True)
        
        if result and result['date']:
            st.success(f"✅ {result['numar_bookmakeri']} intrări extrase!")
            
            # AFIȘEAZĂ LISTA BOOKMAKERILOR
            st.subheader("📋 Bookmakeri găsiți:")
            st.write(result['bookmakers_lista'])
            
            # AFIȘEAZĂ TOATE DATELE
            df = pd.DataFrame(result['date'])
            st.dataframe(df, width='stretch')
            
            # FILTRARE DUPĂ BOOKMAKER
            selected_bookmaker = st.selectbox(
                "Alege un bookmaker:",
                options=["Toți"] + result['bookmakers_lista']
            )
            
            if selected_bookmaker != "Toți":
                filtered_df = df[df['bookmaker'] == selected_bookmaker]
                st.subheader(f"📊 Date pentru {selected_bookmaker}:")
                st.dataframe(filtered_df, width='stretch')
        else:
            st.error("❌ Nu s-au putut extrage datele")
    else:
        st.warning("⚠️ Introdu un URL")
