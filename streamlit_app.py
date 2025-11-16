import streamlit as st
import pandas as pd
from scraper_logic import extract_betano_odds_by_logo, install_playwright

st.set_page_config(page_title="Extractor Betano (Logo)", page_icon="🏀", layout="wide")

st.title("🏀 Extractor Cote Betano (Căutare după LOGO)")
st.write("Acum caută Betano după LOGO-ul său, nu după text")

HEADLESS = True

match_url = st.text_input(
    "🔗 URL meci",
    value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
)

if st.button("🚀 Extrage Cote Betano (LOGO)"):
    if match_url:
        with st.spinner("Se instalează Playwright..."):
            install_playwright()
        
        with st.spinner("Se caută Betano după LOGO..."):
            results = extract_betano_odds_by_logo(match_url, headless=HEADLESS)
        
        if results:
            st.success(f"✅ BETANO GĂSIT! {len(results)} linii cu cote")
            
            df = pd.DataFrame(results)
            st.dataframe(
                df.style.format({
                    'over_closing': '{:.2f}',
                    'under_closing': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descarcă CSV",
                csv,
                "betano_odds.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.error("❌ Betano nu a fost găsit în nicio linie")
    else:
        st.warning("⚠️ Introdu un URL")

st.write("---")
st.write("**Acum caută:** 🖼️ Logo-ul Betano (`img[alt='Betano.ro']`)")
