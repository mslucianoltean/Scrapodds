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

    def open_lines_section(self):
        """Deschide secțiunea cu liniile"""
        try:
            st.info("🎯 Deschid secțiunea cu liniile...")
            xpath = '//*[@id="app"]/div,[object Object],/div,[object Object],/div/main/div,[object Object],/div,[object Object],/div,[object Object],/div,[object Object],/div,[object Object],/ul/li,[object Object],/a/div'
            element = self.wait.until(lambda driver: driver.find_element(By.XPATH, xpath))
            element.click()
            time.sleep(3)
            st.success("✅ Secțiunea cu liniile deschisă cu succes!")
            return True
        except Exception as e:
            st.error(f"❌ Eroare la deschiderea secțiunii: {str(e)}")
            return False

    def scrape_market(self, url, lines_dict):
        """Scrape market cu un singur URL"""
        st.info(f"🌐 Accesez: {url}")
        self.driver.get(url)
        time.sleep(4)
        
        # Deschide secțiunea cu liniile
        if not self.open_lines_section():
            return {}
        
        results = {}
        progress_bar = st.progress(0)
        total_lines = len(lines_dict)
        
        for idx, (line_code, line_value) in enumerate(lines_dict.items()):
            with st.expander(f"🔄 Procesez linia {line_code.upper()}: {line_value}", expanded=True):
                # Setează cheile pentru rezultate
                line_key = line_code
                opening_key = f"{line_code}o"
                closing_key = f"{line_code}c"
                
                results[line_key] = line_value
                
                # Găsește și click pe linia corectă
                odds_data = self.get_odds_for_line(line_value)
                
                if odds_data:
                    results[opening_key] = odds_data['option1']['opening']
                    results[closing_key] = odds_data['option1']['closing']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"📈 Opening: {odds_data['option1']['opening']}")
                    with col2:
                        st.success(f"📉 Closing: {odds_data['option1']['closing']}")
                else:
                    results[opening_key] = None
                    results[closing_key] = None
                    st.error("❌ Nu s-au găsit cotele")
                
                progress_bar.progress((idx + 1) / total_lines)
                time.sleep(2)
        
        return results

    def find_line_in_section(self, line_value):
        """Găsește linia în secțiunea specificată"""
        try:
            line_str = str(line_value)
            st.write(f"🔍 Caut linia: {line_str}")
            
            # Xpath-ul specific pentru căutarea liniilor
            lines_container_xpath = "/html/body/div,[object Object],/div,[object Object],/div,[object Object],/div/main/div,[object Object],/div,[object Object],/div,[object Object],/div,[object Object],/div,[object Object],/div/div,[object Object],/p,[object Object],"
            
            # Caută în containerul de linii
            try:
                lines_container = self.driver.find_element(By.XPATH, lines_container_xpath)
                st.write("✅ Container de linii găsit")
            except:
                st.warning("⚠️ Nu s-a găsit containerul principal, încerc alte metode...")
                lines_container = None
            
            # Diverse selectors pentru găsirea liniei
            selectors = [
                f"//tr//td[contains(text(), '{line_str}')]",
                f"//tr//span[contains(text(), '{line_str}')]",
                f"//p[contains(text(), '{line_str}')]",
                f"//div[contains(text(), '{line_str}')]",
                f"//tr[contains(., '{line_str}')]//td,[object Object],",
                f"//*[contains(text(), '{line_str}')]"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if line_str in element.text and element.is_displayed():
                            st.write(f"✅ Linia găsită cu selector: {selector}")
                            return element
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            st.error(f"❌ Eroare la căutarea liniei: {str(e)}")
            return None

    def get_odds_for_line(self, line_value):
        """Obține cotele pentru o linie specifică"""
        try:
            # Găsește și click pe linie
            line_element = self.find_line_in_section(line_value)
            if not line_element:
                st.warning(f"⚠️ Nu s-a găsit linia {line_value}")
                return None
            
            # Click pe linie
            try:
                line_element.click()
            except:
                # Dacă click direct nu funcționează, încearcă pe rândul părinte
                try:
                    row = line_element.find_element(By.XPATH, "./ancestor::tr")
                    row.click()
                except:
                    self.actions.move_to_element(line_element).click().perform()
            
            st.write("✅ Click pe linie efectuat")
            time.sleep(2)
            
            # Găsește rândul Betano
            betano_row = self.find_betano_row()
            if not betano_row:
                st.warning("⚠️ Nu s-a găsit Betano")
                return None
            
            st.write("✅ Betano găsit")
            
            # Găsește celulele cu cote
            odds_cells = self.find_odds_cells(betano_row)
            if len(odds_cells) < 2:
                st.warning("⚠️ Nu s-au găsit 2 celule cu cote")
                return None
            
            st.write(f"✅ Găsite {len(odds_cells)} celule cu cote")
            
            # Extrage cotele prin hover - AICI ERA EROAREA
            st.write("🔄 Hover pe prima cotă...")
            self.actions.move_to_element(odds_cells,[object Object],).perform()
            time.sleep(2)
            option1_opening, option1_closing = self.extract_odds_from_popup()
            
            st.write("🔄 Hover pe a doua cotă...")
            self.actions.move_to_element(odds_cells,[object Object],).perform()
            time.sleep(2)
            option2_opening, option2_closing = self.extract_odds_from_popup()
            
            return {
                'option1': {'opening': option1_opening, 'closing': option1_closing},
                'option2': {'opening': option2_opening, 'closing': option2_closing}
            }
            
        except Exception as e:
            st.error(f"❌ Eroare: {str(e)}")
            return None

    def find_betano_row(self):
        """Găsește rândul cu Betano"""
        try:
            time.sleep(1)
            betano_selectors = [
                "//tr[contains(., 'Betano')]",
                "//div[contains(text(), 'Betano')]/ancestor::tr",
                "//span[contains(text(), 'Betano')]/ancestor::tr",
                "//a[contains(text(), 'Betano')]/ancestor::tr",
                "//*[contains(text(), 'Betano')]/ancestor::tr"
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
        """Găsește celulele cu cote din rândul Betano"""
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
        """Extrage cotele din popup-ul care apare la hover"""
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
                closing = all_odds,[object Object],
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
    st.header("📋 Instrucțiuni")
    st.markdown("""
    1. 🌐 Introdu URL-ul pentru pagina cu cote
    2. 📝 Completează valorile pentru cele 7 linii
    3. ▶️ Apasă **Start Scraping**
    4. ⏳ Așteaptă procesarea
    5. 📥 Descarcă JSON sau copiază datele
    """)
    
    if 'scraped_data' in st.session_state:
        st.success("✅ Date disponibile!")
        if st.button("🗑️ Șterge date", type="secondary"):
            del st.session_state['scraped_data']
            st.rerun()

# Main content
tab1, tab2 = st.tabs(["📝 Input", "📊 Rezultate"])

with tab1:
    # URL
    st.subheader("🌐 URL")
    main_url = st.text_input("URL pagina cu cote:", key="main_url", placeholder="https://...")
    
    # Lines
    st.subheader("📈 Linii")
    line_cols = st.columns(7)
    line_codes = ['cl', 'm3', 'm2', 'm1', 'p1', 'p2', 'p3']
    lines = {}
    
    for i, code in enumerate(line_codes):
        with line_cols[i]:
            value = st.text_input(code.upper(), key=f"line_{code}", placeholder="Ex: 220.5")
            if value:
                lines[code] = value
    
    # Start button
    st.markdown("---")
    if st.button("▶️ Start Scraping", type="primary", use_container_width=True):
        if not main_url:
            st.error("❌ Introdu URL-ul!")
        elif len(lines) != 7:
            st.error("❌ Trebuie să introduci toate cele 7 linii!")
        else:
            with st.spinner("🔄 Scraping în progres..."):
                scraper = OddsportalScraper()
                try:
                    results = scraper.scrape_market(main_url, lines)
                    st.session_state['scraped_data'] = results
                    st.success("✅ Scraping completat cu succes!")
                    st.balloons()
                finally:
                    scraper.close()

with tab2:
    if 'scraped_data' in st.session_state:
        data = st.session_state['scraped_data']
        
        # Display în tabel
        st.subheader("📊 Rezultate")
        display_data = []
        for code in line_codes:
            display_data.append({
                'Linie': code.upper(),
                'Valoare': data.get(code),
                'Opening': data.get(f'{code}o'),
                'Closing': data.get(f'{code}c')
            })
        
        st.table(display_data)
        
        # JSON Display
        st.markdown("---")
        st.subheader("📋 Date JSON (pentru Pydroid)")
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        st.code(json_str, language='json')
        
        # Download button
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name="odds_data.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("ℹ️ Completează datele în tab-ul Input și apasă Start Scraping")
