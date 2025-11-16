import streamlit as st
import pandas as pd
from scraper_logic import scrape_betano_odds, validate_url, add_over_under_hash

# Configurare pagină
st.set_page_config(
    page_title="OddsPortal Betano Scraper",
    page_icon="🏀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🏀 OddsPortal Betano Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extrage automat cotele Opening și Closing de la Betano pentru piața Over/Under</div>', unsafe_allow_html=True)

st.markdown("---")

# Sidebar pentru setări
with st.sidebar:
    st.header("⚙️ Setări")
    
    show_browser = st.checkbox(
        "Arată browser",
        value=False,
        help="Pornește browser-ul vizibil (util pentru debugging)"
    )
    
    auto_fix_url = st.checkbox(
        "Auto-fix URL",
        value=True,
        help="Adaugă automat #over-under;1 dacă lipsește"
    )
    
    st.markdown("---")
    
    st.subheader("📖 Ghid rapid")
    st.markdown("""
    1. Copiază URL-ul meciului
    2. Asigură-te că include `#over-under`
    3. Click pe "Extrage Cote"
    4. Așteaptă 10-20 secunde
    5. Descarcă rezultatele
    """)

# Input principal
col1, col2 = st.columns([4, 1])

with col1:
    match_url = st.text_input(
        "🔗 URL complet al meciului",
        value="https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#over-under;1",
        help="Copiază URL-ul din browser - trebuie să conțină #over-under",
        placeholder="https://www.oddsportal.com/.../match-id/#over-under;1"
    )

with col2:
    st.write("")
    st.write("")
    if st.button("🔄 Reset", use_container_width=True):
        st.rerun()

# Validare și auto-fix URL
if match_url:
    if not validate_url(match_url):
        st.error("❌ URL invalid! Trebuie să fie de pe oddsportal.com")
    elif '#over-under' not in match_url:
        if auto_fix_url:
            match_url = add_over_under_hash(match_url)
            st.success(f"✓ URL actualizat: `{match_url}`")
        else:
            st.warning("⚠️ URL-ul ar trebui să conțină #over-under")

st.markdown("---")

# Buton principal
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    scrape_button = st.button(
        "🚀 Extrage Cote Betano",
        type="primary",
        use_container_width=True,
        disabled=not match_url or not validate_url(match_url)
    )

# Proces de scraping
if scrape_button:
    # Container pentru progress
    progress_container = st.container()
    
    with progress_container:
        progress_placeholder = st.empty()
        
        def update_progress(msg):
            progress_placeholder.info(msg)
        
        # Rulează scraper-ul
        with st.spinner("⏳ Scraping în progres... (poate dura până la 30 de secunde)"):
            results = scrape_betano_odds(
                match_url,
                headless=not show_browser,
                progress_callback=update_progress
            )
        
        # Clear progress
        progress_placeholder.empty()
    
    # Afișează rezultatele
    if results:
        st.success("✅ Scraping finalizat cu succes!")
        
        st.markdown("---")
        st.subheader("📊 Cote Betano - Over/Under")
        
        # Creează DataFrame
        df = pd.DataFrame(results)
        
        # Metrici
        cols = st.columns(len(results))
        
        for idx, (col, row) in enumerate(zip(cols, results)):
            with col:
                st.markdown(f"### {row['type']}")
                st.metric("Over", f"{row['over']:.2f}")
                st.metric("Under", f"{row['under']:.2f}")
        
        st.markdown("---")
        
        # Tabel detaliat
        st.dataframe(
            df.style.format({'over': '{:.2f}', 'under': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Export
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descarcă CSV",
                csv,
                "betano_odds.csv",
                "text/csv",
                use_container_width=True
            )
        
        # Comparație Opening vs Closing
        if len(results) == 2:
            st.markdown("---")
            st.subheader("📈 Comparație Opening vs Closing")
            
            opening = next(r for r in results if r['type'] == 'Opening')
            closing = next(r for r in results if r['type'] == 'Closing')
            
            col1, col2 = st.columns(2)
            
            with col1:
                diff_over = closing['over'] - opening['over']
                st.metric(
                    "Diferență Over",
                    f"{diff_over:+.2f}",
                    delta=f"{(diff_over/opening['over']*100):+.1f}%"
                )
            
            with col2:
                diff_under = closing['under'] - opening['under']
                st.metric(
                    "Diferență Under",
                    f"{diff_under:+.2f}",
                    delta=f"{(diff_under/opening['under']*100):+.1f}%"
                )
    
    else:
        st.error("❌ Nu s-au putut extrage datele")
        
        with st.expander("🔍 Posibile cauze"):
            st.markdown("""
            - **Betano nu are cote** pentru acest meci
            - **URL-ul este incorect** - verifică că meciul există
            - **Structura paginii** s-a schimbat - scraper-ul trebuie actualizat
            - **Protecție anti-bot** - OddsPortal blochează request-ul
            - **Conexiune lentă** - încearcă din nou
            
            **Soluții:**
            1. Verifică manual în browser că Betano apare în listă
            2. Bifează "Arată browser" pentru debugging
            3. Încearcă alt meci
            """)

# Footer
st.markdown("---")

with st.expander("ℹ️ Informații și Help"):
    tab1, tab2, tab3 = st.tabs(["Cum funcționează", "Instalare", "Troubleshooting"])
    
    with tab1:
        st.markdown("""
        ### 🔄 Procesul de scraping:
        
        1. **Browser automat** - Deschide pagina în Chromium
        2. **Navighează** - Merge la tab-ul Over/Under
        3. **Găsește Betano** - Caută rândul bookmaker-ului
        4. **Extrage Closing** - Citește cotele vizibile
        5. **Click & Extract Opening** - Deschide popup-ul pentru opening odds
        6. **Returnează datele** - Structurate și formatate
        """)
    
    with tab2:
        st.markdown("""
        ### 📦 Instalare locală:
        
        ```bash
        pip install streamlit playwright pandas
        playwright install chromium
        ```
        
        ### ☁️ Deploy pe Streamlit Cloud:
        
        **requirements.txt:**
        ```
        streamlit
        playwright==1.56.0
        pandas
        ```
        
        **packages.txt:**
        ```
        chromium
        chromium-chromedriver
        ```
        """)
    
    with tab3:
        st.markdown("""
        ### 🔧 Probleme comune:
        
        **"Nu găsește rândul Betano"**
        - Verifică că Betano chiar apare în listă pe site
        - Încearcă cu "Arată browser" activ
        
        **"Timeout / Pagina nu se încarcă"**
        - Conexiune lentă - măre timeout-ul în cod
        - OddsPortal blochează - schimbă User-Agent
        
        **"Nu extrage opening odds"**
        - Popup-ul are structură diferită
        - Verifică în DevTools cum arată popup-ul
        
        **Pe Streamlit Cloud nu funcționează**
        - Verifică că ai `packages.txt` cu chromium
        - Restart app după deploy
        """)

st.markdown("---")
st.caption("Made with ❤️ using Streamlit & Playwright | © 2024")
