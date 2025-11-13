# ============================================================
# FIȘIER 1: streamlit_app.py
# Pune acest fișier în GitHub repo
# ============================================================

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import re

class OddsportalScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.actions = ActionChains(self.driver)
    
    def scrape_market(self, url, lines_dict, market_prefix):
        st.info(f"🔗 Accesez: {url}")
        self.driver.get(url)
        time.sleep(4)
        
        results = {}
        progress_bar = st.progress(0)
        total_lines = len(lines_dict)
        
        for idx, (line_code, line_value) in enumerate(lines_dict.items()):
            with st.expander(f"📍 Procesez linia {line_code.upper()}: {line_value}", expanded=True):
                line_key = line_code if market_prefix == 'c' else f"h{line_code}"
                option1_opening_key = f"{market_prefix}{line_code}o"
                option1_closing_key = f"{market_prefix}{line_code}c"
                
                results[line_key] = line_value
                
                odds_data = self.get_odds_for_line(line_value)
                
                if odds_data:
                    results[option1_opening_key] = odds_data['option1']['opening']
                    results[option1_closing_key] = odds_data['option1']['closing']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"✅ Opening: {odds_data['option1']['opening']}")
                    with col2:
                        st.success(f"✅ Closing: {odds_data['option1']['closing']}")
                else:
                    results[option1_opening_key] = None
                    results[option1_closing_key] = None
                    st.error("❌ Nu s-au găsit cotele")
                
                progress_bar.progress((idx + 1) / total_lines)
                time.sleep(2)
        
        return results
    
    def get_odds_for_line(self, line_value):
        try:
            line_str = str(line_value)
            st.write(f"🔍 Caut linia: {line_str}")
            
            line_element = self.find_and_click_line(line_str)
            if not line_element:
                st.warning(f"⚠️ Nu s-a găsit linia {line_str}")
                return None
            
            st.write("✅ Click pe linie efectuat")
            time.sleep(2)
            
            betano_row = self.find_betano_row()
            if not betano_row:
                st.warning("⚠️ Nu s-a găsit Betano")
                return None
            
            st.write("✅ Betano găsit")
            
            odds_cells = self.find_odds_cells(betano_row)
            if len(odds_cells) < 2:
                st.warning("⚠️ Nu s-au găsit 2 celule cu cote")
                return None
            
            st.write(f"✅ Găsite {len(odds_cells)} celule cu cote")
            
            st.write("🖱️ Hover pe prima cotă...")
            self.actions.move_to_element(odds_cells[0]).perform()
            time.sleep(2)
            option1_opening, option1_closing = self.extract_odds_from_popup()
            
            st.write("🖱️ Hover pe a doua cotă...")
            self.actions.move_to_element(odds_cells[1]).perform()
            time.sleep(2)
            option2_opening, option2_closing = self.extract_odds_from_popup()
            
            return {
                'option1': {'opening': option1_opening, 'closing': option1_closing},
                'option2': {'opening': option2_opening, 'closing': option2_closing}
            }
            
        except Exception as e:
            st.error(f"❌ Eroare: {str(e)}")
            return None
    
    def find_and_click_line(self, line_str):
        try:
            selectors = [
                f"//tr//td[contains(text(), '{line_str}')]",
                f"//tr//span[contains(text(), '{line_str}')]",
                f"//tr[contains(., '{line_str}')]//td[1]",
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if line_str in element.text:
                            try:
                                element.click()
                            except:
                                row = element.find_element(By.XPATH, "./ancestor::tr")
                                row.click()
                            return element
                except:
                    continue
            return None
        except Exception as e:
            return None
    
    def find_betano_row(self):
        try:
            time.sleep(1)
            betano_selectors = [
                "//tr[contains(., 'Betano')]",
                "//div[contains(text(), 'Betano')]/ancestor::tr",
                "//span[contains(text(), 'Betano')]/ancestor::tr",
                "//a[contains(text(), 'Betano')]/ancestor::tr",
            ]
            
            for selector in betano_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and 'betano' in element.text.lower():
                            return element
                except:
                    continue
            return None
        except Exception as e:
            return None
    
    def find_odds_cells(self, betano_row):
        try:
            cells = betano_row.find_elements(By.XPATH, ".//td")
            odds_cells = []
            for cell in cells:
                text = cell.text.strip()
                if re.match(r'^\d+\.?\d*$', text):
                    odds_cells.append(cell)
            return odds_cells[:2] if len(odds_cells) >= 2 else odds_cells
        except Exception as e:
            return []
    
    def extract_odds_from_popup(self):
        try:
            time.sleep(1)
            popup_selectors = [
                "//div[contains(@class, 'popup') and contains(@style, 'display')]",
                "//div[contains(@class, 'tooltip')]",
                "//div[contains(@class, 'odds-popup')]",
                "//div[@role='tooltip']",
                "//div[contains(@id, 'popup')]",
            ]
            
            popup_text = None
            for selector in popup_selectors:
                try:
                    popups = self.driver.find_elements(By.XPATH, selector)
                    for popup in popups:
                        if popup.is_displayed():
                            popup_text = popup.text
                            if popup_text and len(popup_text) > 5:
                                break
                    if popup_text:
                        break
                except:
                    continue
            
            if not popup_text:
                return None, None
            
            lines = [l.strip() for l in popup_text.split('\n') if l.strip()]
            
            closing = None
            opening = None
            all_odds = []
            
            for line in lines:
                matches = re.findall(r'\b(\d+\.\d+)\b', line)
                all_odds.extend(matches)
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                if any(kw in line_lower for kw in ['closing', 'închidere', 'inchidere', 'current', 'latest']):
                    for search_line in lines[max(0,i-1):min(i+2, len(lines))]:
                        match = re.search(r'\b(\d+\.\d+)\b', search_line)
                        if match:
                            closing = match.group(1)
                            break
                
                if any(kw in line_lower for kw in ['opening', 'deschidere', 'start']) or '/' in line or '-' in line:
                    for search_line in lines[i:min(i+3, len(lines))]:
                        match = re.search(r'\b(\d+\.\d+)\b', search_line)
                        if match:
                            opening = match.group(1)
                            break
            
            if not closing and len(all_odds) > 0:
                closing = all_odds[0]
            if not opening and len(all_odds) > 1:
                opening = all_odds[-1]
            
            return opening, closing
            
        except Exception as e:
            return None, None
    
    def close(self):
        self.driver.quit()


# STREAMLIT UI
st.set_page_config(page_title="🏀 Oddsportal Scraper", page_icon="🏀", layout="wide")

st.title("🏀 Oddsportal Basketball Scraper")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("ℹ️ Instrucțiuni")
    st.markdown("""
    1. Introdu URL-urile pentru Over/Under și Handicap
    2. Completează valorile pentru cele 7 linii
    3. Apasă **Start Scraping**
    4. Așteaptă procesarea
    5. Descarcă JSON sau copiază datele
    """)
    
    if 'scraped_data' in st.session_state:
        st.success("✅ Date disponibile!")
        if st.button("🗑️ Șterge date", type="secondary"):
            del st.session_state['scraped_data']
            st.rerun()

# Main content
tab1, tab2 = st.tabs(["📝 Input", "📊 Rezultate"])

with tab1:
    # URLs
    st.subheader("🔗 URL-uri")
    col1, col2 = st.columns(2)
    with col1:
        over_under_url = st.text_input("Over/Under URL:", key="ou_url")
    with col2:
        handicap_url = st.text_input("Handicap URL:", key="hc_url")
    
    # Over/Under Lines
    st.subheader("📊 Over/Under - Linii")
    ou_cols = st.columns(7)
    line_codes = ['cl', 'm3', 'm2', 'm1', 'p1', 'p2', 'p3']
    ou_lines = {}
    
    for i, code in enumerate(line_codes):
        with ou_cols[i]:
            value = st.text_input(code.upper(), key=f"ou_{code}")
            if value:
                ou_lines[code] = value
    
    # Handicap Lines
    st.subheader("📊 Handicap - Linii")
    hc_cols = st.columns(7)
    hc_lines = {}
    
    for i, code in enumerate(line_codes):
        with hc_cols[i]:
            value = st.text_input(code.upper(), key=f"hc_{code}")
            if value:
                hc_lines[code] = value
    
    # Start button
    st.markdown("---")
    if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
        if not over_under_url or not handicap_url:
            st.error("❌ Introdu ambele URL-uri!")
        elif len(ou_lines) != 7 or len(hc_lines) != 7:
            st.error("❌ Trebuie să introduci toate cele 7 linii pentru fiecare piață!")
        else:
            with st.spinner("🔄 Scraping în progres..."):
                scraper = OddsportalScraper()
                try:
                    st.subheader("📊 Over/Under")
                    ou_results = scraper.scrape_market(over_under_url, ou_lines, 'c')
                    
                    st.subheader("📊 Handicap")
                    hc_results = scraper.scrape_market(handicap_url, hc_lines, 'h')
                    
                    final_results = {**ou_results, **hc_results}
                    st.session_state['scraped_data'] = final_results
                    
                    st.success("✅ Scraping completat cu succes!")
                    st.balloons()
                    
                finally:
                    scraper.close()

with tab2:
    if 'scraped_data' in st.session_state:
        data = st.session_state['scraped_data']
        
        # Display în tabele
        st.subheader("📊 Over/Under")
        ou_display = []
        for code in line_codes:
            ou_display.append({
                'Linie': code.upper(),
                'Valoare': data.get(code),
                'Opening': data.get(f'c{code}o'),
                'Closing': data.get(f'c{code}c')
            })
        st.table(ou_display)
        
        st.subheader("📊 Handicap")
        hc_display = []
        for code in line_codes:
            hc_display.append({
                'Linie': code.upper(),
                'Valoare': data.get(f'h{code}'),
                'Opening': data.get(f'h{code}o'),
                'Closing': data.get(f'h{code}c')
            })
        st.table(hc_display)
        
        # JSON Display - IMPORTANT PENTRU PYDROID!
        st.markdown("---")
        st.subheader("📥 Date JSON (pentru Pydroid)")
        
        # Afișare JSON într-un format ușor de extras
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        st.code(json_str, language='json')
        
        # Download button
        st.download_button(
            label="💾 Download JSON",
            data=json_str,
            file_name="odds_data.json",
            mime="application/json",
            use_container_width=True
        )
        
    else:
        st.info("👈 Completează datele în tab-ul Input și apasă Start Scraping")


