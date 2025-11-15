import streamlit as st
import json
from scraper_logic import scrape_basketball_match_fixed

st.title("🏀 OddsPortal Scraper Betano")

# Input pentru link-uri
ou_link = st.text_input("Over/Under Link", "https://www.oddsportal.com/basketball/usa/nba/los-angeles-lakers-milwaukee-bucks-h1eGdE3C/")
ah_link = st.text_input("Asian Handicap Link", "https://www.oddsportal.com/basketball/usa/nba/los-angeles-lakers-milwaukee-bucks-h1eGdE3C/#ah;1;3.5;0")

if st.button("🚀 Start Scraping"):
    with st.spinner("Scraping in progress..."):
        results = scrape_basketball_match_fixed(ou_link, ah_link)
        
        if results['Error']:
            st.error(f"Error: {results['Error']}")
        else:
            st.success("Scraping completed!")
            
            # Afișează rezultatele Over/Under
            st.subheader("📊 Over/Under Lines")
            if results['Over_Under_Lines']:
                for line in results['Over_Under_Lines']:
                    st.write(f"**Line {line['Line']}**: Over {line['Over_Close']} | Under {line['Under_Close']}")
            else:
                st.info("No Over/Under lines found")
            
            # Afișează rezultatele Asian Handicap
            st.subheader("🎯 Asian Handicap Lines")
            if results['Handicap_Lines']:
                for line in results['Handicap_Lines']:
                    st.write(f"**Line {line['Line']}**: Home {line['Home_Close']} | Away {line['Away_Close']}")
            else:
                st.info("No Asian Handicap lines found")
            
            # Debug info
            st.subheader("🔍 Debug Info")
            st.json(results['Debug'])
