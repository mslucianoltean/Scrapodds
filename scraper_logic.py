import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING COMPLET CU EXTRAGERE COTE BETANO
    """
    
    results = {
        'Match': 'Scraping Complet cu Cote',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING COMPLET ===")
        
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
        
        # Folosește Chromium din sistem
        options.binary_location = "/usr/bin/chromium"
        chromedriver_path = "/usr/bin/chromedriver"
        
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        # Ascunde automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser pornit cu succes!")
        
        # FUNCȚIE ÎMBUNĂTĂȚITĂ PENTRU EXTRAGERE COTE
        def extract_betano_odds_improved():
            """Extrage cotele Betano cu multiple strategii"""
            over_odd, under_odd = 'N/A', 'N/A'
            betano_found = False
            
            # METODA 1: Caută link Betano și extrage din rând
            betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
            print(f"    🔍 Elemente Betano găsite: {len(betano_elements)}")
            
            for betano_element in betano_elements:
                try:
                    # Mergi în sus în ierarhie să găsești rândul
                    current_element = betano_element
                    betano_row = None
                    
                    for _ in range(6):  # Încearcă până la 6 niveluri în sus
                        try:
                            current_element = current_element.find_element(By.XPATH, "./..")
                            if current_element.tag_name == 'tr':
                                betano_row = current_element
                                break
                        except:
                            break
                    
                    if betano_row:
                        # Încearcă multiple selectori pentru cote
                        odds_selectors = [
                            ".//p[contains(@class, 'odds-text')]",
                            ".//p[contains(@class, 'odds')]",
                            ".//span[contains(@class, 'odds')]",
                            ".//div[contains(@class, 'odds')]",
                            ".//*[contains(@class, 'odds-text line-through')]",
                            ".//p | .//span | .//div"  # Fallback - toate elementele
                        ]
                        
                        for selector in odds_selectors:
                            try:
                                odds_elements = betano_row.find_elements(By.XPATH, selector)
                                if len(odds_elements) >= 2:
                                    # Filtrează doar elementele care arată a cote
                                    valid_odds = []
                                    for odds_elem in odds_elements:
                                        odds_text = odds_elem.text.strip()
                                        # Verifică dacă textul arată a cotă (conține cifre și punct)
                                        if (any(c.isdigit() for c in odds_text) and 
                                            '.' in odds_text and 
                                            len(odds_text) <= 6):  # Cotele sunt scurte
                                            valid_odds.append(odds_text)
                                    
                                    if len(valid_odds) >= 2:
                                        over_odd = valid_odds[0]
                                        under_odd = valid_odds[1]
                                        print(f"    ✅ COTE EXTRASE: Over={over_odd}, Under={under_odd}")
                                        betano_found = True
                                        break
                            except:
                                continue
                        
                        if betano_found:
                            break
                            
                except Exception as e:
                    continue
            
            # METODA 2: Caută prin tot HTML-ul
            if not betano_found:
                page_source = driver.page_source
                if 'betano' in page_source.lower():
                    print("    ℹ️ Betano în pagină - încerc strategie alternativă")
                    
                    # Caută secțiuni cu Betano și elemente apropiate
                    betano_sections = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'betano')]")
                    
                    for section in betano_sections[:3]:
                        try:
                            # Caută elemente cu numere în apropiere
                            nearby_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '.') and number(translate(substring-before(concat(text(), '.'), '.', ''))]")
                            
                            potential_odds = []
                            for elem in nearby_elements:
                                text = elem.text.strip()
                                if ('.' in text and 
                                    any(c.isdigit() for c in text) and 
                                    len(text) <= 6 and
                                    text.count('.') == 1):
                                    potential_odds.append(text)
                            
                            if len(potential_odds) >= 2:
                                over_odd = potential_odds[0]
                                under_odd = potential_odds[1]
                                print(f"    ✅ COTE ALTERNATIVE: Over={over_odd}, Under={under_odd}")
                                betano_found = True
                                break
                                
                        except:
                            continue
            
            return over_odd, under_odd
        
        # OVER/UNDER - EXTRAGERE LINII ȘI COTE
        print("🔍 OVER/UNDER - Încep extragerea...")
        driver.get(ou_link)
        
        # Așteaptă generos pentru încărcare
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(10)
        
        ou_lines = []
        
        # Caută toate elementele care conțin "Over/Under"
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        print(f"📊 Elemente Over/Under găsite: {len(all_elements)}")
        
        # Procesează fiecare element
        processed_lines = set()
        
        for i, element in enumerate(all_elements[:20]):
            try:
                text = element.text.strip()
                if text and 'Over/Under' in text:
                    print(f"  {i+1}. {text}")
                    
                    # Extrage valoarea liniei
                    match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        
                        # Evită duplicate
                        if line_val in processed_lines:
                            continue
                        processed_lines.add(line_val)
                        
                        display_line = f"+{line_val}"
                        print(f"  ✅ LINIE EXTRASĂ: {display_line}")
                        
                        # Construiește URL direct
                        base_url = ou_link.split('#')[0]
                        direct_url = f"{base_url}#over-under;1;{line_val};0"
                        
                        # Navighează la URL-ul direct pentru cote
                        print(f"  📡 Accesez URL pentru cote...")
                        driver.get(direct_url)
                        time.sleep(8)
                        
                        # Extrage cotele Betano
                        over_odd, under_odd = extract_betano_odds_improved()
                        
                        # Salvează rezultatul
                        ou_lines.append({
                            'Line': display_line,
                            'Over_Close': over_odd,
                            'Under_Close': under_odd,
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                        
                        # Revino la pagina principală
                        driver.get(ou_link)
                        time.sleep(5)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare element {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP - EXTRAGERE LINII ȘI COTE
        print("\n🔍 ASIAN HANDICAP - Încep extragerea...")
        driver.get(ah_link)
        time.sleep(10)
        
        ah_lines = []
        
        # Caută elementele Asian Handicap
        ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
        
        # Procesează fiecare element AH
        processed_ah_lines = set()
        
        for i, element in enumerate(ah_elements[:15]):
            try:
                text = element.text.strip()
                if text and 'Asian Handicap' in text:
                    print(f"  {i+1}. {text}")
                    
                    # Extrage valoarea liniei
                    match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        
                        # Evită duplicate
                        if line_val in processed_ah_lines:
                            continue
                        processed_ah_lines.add(line_val)
                        
                        clean_val = line_val.replace('+', '').replace('-', '')
                        print(f"  ✅ LINIE AH EXTRASĂ: {line_val}")
                        
                        # Construiește URL direct
                        base_url = ah_link.split('#')[0]
                        direct_url = f"{base_url}#ah;1;{clean_val};0"
                        
                        # Navighează la URL-ul direct pentru cote
                        print(f"  📡 Accesez URL AH pentru cote...")
                        driver.get(direct_url)
                        time.sleep(8)
                        
                        # Extrage cotele Betano (folosește aceeași logică)
                        home_odd, away_odd = extract_betano_odds_improved()
                        
                        # Salvează rezultatul
                        ah_lines.append({
                            'Line': line_val,
                            'Home_Close': home_odd,
                            'Away_Close': away_odd,
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                        
                        # Revino la pagina principală
                        driver.get(ah_link)
                        time.sleep(5)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare AH {i+1}: {e}")
                continue
        
        # SALVARE REZULTATE
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'unique_ou_lines': list(processed_lines),
            'unique_ah_lines': list(processed_ah_lines),
            'strategy': 'Extracție completă cu cote Betano',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLETAT: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Browser închis")
    
    return results
