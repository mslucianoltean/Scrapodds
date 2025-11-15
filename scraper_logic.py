import requests
from bs4 import BeautifulSoup
import re
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING CU SELENIUM SIMPLU ȘI SIGUR
    """
    
    results = {
        'Match': 'Scraping cu Selenium',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING CU SELENIUM ===")
        
        # Configurare browser pentru Streamlit Cloud
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Folosește webdriver-manager pentru a gestiona driver-ul
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Ascunde că e automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # OVER/UNDER
        print("🔍 Accesez pagina Over/Under...")
        driver.get(ou_link)
        
        # Așteaptă să se încarce
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Așteaptă JavaScript
        time.sleep(8)
        
        # Salvează HTML pentru debug
        html_content = driver.page_source
        print(f"📄 Lungime HTML: {len(html_content)} caractere")
        
        # Verifică ce conține pagina
        if 'Over/Under' in html_content:
            print("✅ 'Over/Under' găsit în HTML!")
        else:
            print("❌ 'Over/Under' NU găsit în HTML")
            print("📝 Primele 1000 caractere:", html_content[:1000])
        
        # Caută liniile Over/Under
        ou_lines = []
        
        # Încearcă să găsească elementele care conțin "Over/Under"
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
            print(f"🔍 Elemente cu 'Over/Under' găsite: {len(elements)}")
            
            for i, element in enumerate(elements[:10]):
                try:
                    text = element.text.strip()
                    print(f"  {i+1}. Text: {text}")
                    
                    # Extrage valoarea liniei
                    match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        display_line = f"+{line_val}"
                        print(f"  ✅ LINIE EXTRASĂ: {display_line}")
                        
                        # Construiește URL direct
                        base_url = ou_link.split('#')[0]
                        direct_url = f"{base_url}#over-under;1;{line_val};0"
                        
                        # Navighează la URL-ul direct
                        print(f"  📡 Accesez URL direct: {direct_url}")
                        driver.get(direct_url)
                        time.sleep(5)
                        
                        # Caută Betano
                        betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                        print(f"  🔍 Elemente Betano găsite: {len(betano_elements)}")
                        
                        over_odd, under_odd = 'N/A', 'N/A'
                        
                        if betano_elements:
                            # Încearcă să găsești rândul Betano
                            try:
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                                
                                if len(odds_elements) >= 2:
                                    over_odd = odds_elements[0].text.strip()
                                    under_odd = odds_elements[1].text.strip()
                                    print(f"  ✅ COTE: Over={over_odd}, Under={under_odd}")
                            except Exception as e:
                                print(f"  ⚠️ Eroare extragere cote: {e}")
                        
                        ou_lines.append({
                            'Line': display_line,
                            'Over_Close': over_odd,
                            'Under_Close': under_odd,
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                        
                        # Revino la pagina principală
                        driver.get(ou_link)
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"  ⚠️ Eroare procesare element {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Eroare căutare elemente: {e}")
        
        # ASIAN HANDICAP
        print("\n🔍 Accesez pagina Asian Handicap...")
        driver.get(ah_link)
        time.sleep(8)
        
        ah_lines = []
        
        try:
            ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
            print(f"🔍 Elemente AH găsite: {len(ah_elements)}")
            
            for i, element in enumerate(ah_elements[:5]):
                try:
                    text = element.text.strip()
                    print(f"  {i+1}. Text AH: {text}")
                    
                    match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        clean_val = line_val.replace('+', '').replace('-', '')
                        print(f"  ✅ LINIE AH EXTRASĂ: {line_val}")
                        
                        base_url = ah_link.split('#')[0]
                        direct_url = f"{base_url}#ah;1;{clean_val};0"
                        
                        print(f"  📡 Accesez URL AH: {direct_url}")
                        driver.get(direct_url)
                        time.sleep(5)
                        
                        betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                        print(f"  🔍 Elemente Betano AH: {len(betano_elements)}")
                        
                        home_odd, away_odd = 'N/A', 'N/A'
                        
                        if betano_elements:
                            try:
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                                
                                if len(odds_elements) >= 2:
                                    home_odd = odds_elements[0].text.strip()
                                    away_odd = odds_elements[1].text.strip()
                                    print(f"  ✅ COTE AH: Home={home_odd}, Away={away_odd}")
                            except Exception as e:
                                print(f"  ⚠️ Eroare cote AH: {e}")
                        
                        ah_lines.append({
                            'Line': line_val,
                            'Home_Close': home_odd,
                            'Away_Close': away_odd,
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                        
                        driver.get(ah_link)
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"  ⚠️ Eroare procesare AH {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Eroare căutare AH: {e}")
        
        # Salvează rezultatele
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'strategy': 'Selenium + WebDriver Manager',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ FINAL: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Browser închis")
    
    return results
