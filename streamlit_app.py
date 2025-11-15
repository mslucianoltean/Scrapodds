import streamlit as st
import json
from scraper_logic import scrape_basketball_match_full_data_filtered

st.title("🏀 OddsPortal Scraper")

# Input URL-uri
ou_url = st.text_input("URL Over/Under", "https://www.oddsportal.com/basketball/usa/nba/example")
ah_url = st.text_input("URL Asian Handicap", "https://www.oddsportal.com/basketball/usa/nba/example")

if st.button("Start Scraping"):
    with st.spinner("Scraping in progres..."):
        try:
            results = scrape_basketball_match_full_data_filtered(ou_url, ah_url)
            
            # AFIȘARE SIGURĂ
            st.success("✅ Extracție finalizată!")
            
            # Over/Under
            st.subheader("📊 Over/Under Lines")
            if results['Over_Under_Lines']:
                st.json(results['Over_Under_Lines'])
            else:
                st.info("Nu au fost găsite linii Over/Under.")
            
            # Asian Handicap  
            st.subheader("🎯 Asian Handicap Lines")
            if results['Handicap_Lines']:
                st.json(results['Handicap_Lines'])
            else:
                st.info("Nu au fost găsite linii Asian Handicap.")
            
            # Debug info
            if results.get('Debug'):
                with st.expander("🔍 Debug Info"):
                    st.json(results['Debug'])
                    
            # Eroare
            if results.get('Error'):
                st.error(f"Eroare: {results['Error']}")
                
        except Exception as e:
            st.error(f"Eroare aplicație: {str(e)}")
