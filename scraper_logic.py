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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

def setup_driver():
    """Configurează driver-ul Chrome pentru Streamlit Cloud"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Folosește webdriver_manager pentru a gestiona automat ChromeDriver
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"⚠️ WebDriverManager failed, using system Chrome: {e}")
        # Fallback pentru Streamlit Cloud
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_betano_odds_comprehensive(driver):
    """Extrage cotele Betano folosind multiple strategii"""
    over_odd, under_odd = 'N/A', 'N/A'
    
    print("    🔍 Încep căutarea Betano...")
    
    # Salvează HTML pentru debug
    page_source = driver.page_source
    print(f"    📄 Lungime HTML curent: {len(page_source)} caractere")
    
    # STRATEGIA 1: Caută după logo Betano
    try:
        betano_selectors = [
            "img[src*='betano']",
            "img[alt*='Betano']", 
            "img[title*='Betano']",
            "img[alt*='betano']",
            "//img[contains(@src, 'betano')]",
            "//img[contains(@alt, 'Betano')]"
        ]
        
        for selector in betano_selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"    ✅ Logo Betano găsit cu selector: {selector}")
                    logo = elements[0]
                    
                    # Găsește rândul părinte
                    row = logo.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                    
                    # Extrage cotele
                    odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                    if len(odds_elements) >= 2:
                        over_odd = odds_elements[0].text.strip()
                        under_odd = odds_elements[1].text.strip()
                        print(f"    ✅ COTE BETANO EXTRASE: Over={over_odd}, Under={under_odd}")
                        return over_odd, under_odd
                        
            except Exception as e:
                continue
    except Exception as e:
        print(f"    ⚠️ Eroare strategie logo: {e}")
    
    # STRATEGIA 2: Caută după text Betano
    try:
        betano_text_selectors = [
            "//*[contains(text(), 'Betano')]",
            "//*[contains(text(), 'betano')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'betano')]"
        ]
        
        for selector in betano_text_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"    ✅ Text Betano găsit cu selector: {selector}")
                    
                    for element in elements[:3]:  # Verifică primele 3
                        try:
                            row = element.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                            odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                            
                            if len(odds_elements) >= 2:
                                over_odd = odds_elements[0].text.strip()
                                under_odd = odds_elements[1].text.strip()
                                print(f"    ✅ COTE BETANO (text): Over={over_odd}, Under={under_odd}")
                                return over_odd, under_odd
                        except:
                            continue
            except Exception as e:
                continue
    except Exception as e:
        print(f"    ⚠️ Eroare strategie text: {e}")
    
    # STRATEGIA 3: Caută în toate rândurile expandate
    try:
        expanded_rows = driver.find_elements(By.XPATH, "//div[contains(@data-testid, 'over-under-expanded-row')]")
        print(f"    🔍 Rânduri expandate găsite: {len(expanded_rows)}")
        
        for i, row in enumerate(expanded_rows):
            try:
                row_html = row.get_attribute('innerHTML')
                if 'betano' in row_html.lower():
                    print(f"    ✅ Betano găsit în rândul {i+1}")
                    
                    odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                    if len(odds_elements) >= 2:
                        over_odd = odds_elements[0].text.strip()
                        under_odd = odds_elements[1].text.strip()
                        print(f"    ✅ COTE BETANO (rând {i+1}): Over={over_odd}, Under={under_odd}")
                        return over_odd, under_odd
            except Exception as e:
                continue
    except Exception as e:
        print(f"    ⚠️ Eroare strategie rânduri: {e}")
    
    # STRATEGIA 4: Caută orice cote dacă Betano nu este găsit
    try:
        all_odds = driver.find_elements(By.XPATH, "//p[contains(@class, 'odds-text')]")
        print(f"    🔍 Toate cotele găsite: {len(all_odds)}")
        
        if len(all_odds) >= 2:
            over_odd = all_odds[0].text.strip()
            under_odd = all_odds[1].text.strip()
            print(f"    ⚠️ Cote generale (nu Betano): Over={over_odd}, Under={under_odd}")
    except Exception as e:
        print(f"    ⚠️ Eroare strategie generală: {e}")
    
    return over_odd, under_odd

def scrape_basketball_match_fixed(ou_link, ah_link):
    """
    SCRAPING COMPLET CU GESTIUNE ÎMBUNĂTĂȚITĂ A BETANO
    """
    
    results = {
        'Match': 'Scraping Betano Optimizat',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING BETANO OPTIMIZAT ===")
        
        # Configurează driver-ul
        driver = setup_driver()
        print("✅ Browser pornit cu succes!")
        
        # OVER/UNDER SCRAPING
        print("🔍 OVER/UNDER - Încep extragerea...")
        driver.get(ou_link)
        time.sleep(8)
        
        ou_lines = []
        
        # Găsește toate liniile Over/Under
        ou_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        print(f"📊 Elemente Over/Under găsite: {len(ou_elements)}")
        
        processed_lines = set()
        
        for i, element in enumerate(ou_elements[:10]):  # Limitează la primele 10
            try:
                text = element.text.strip()
                if 'Over/Under' in text and '+' in text:
                    # Extrage valoarea liniei
                    match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        
                        if line_val in processed_lines:
                            continue
                        processed_lines.add(line_val)
                        
                        display_line = f"+{line_val}"
                        print(f"  {i+1}. LINIE OU EXTRASĂ: {display_line}")
                        
                        # Construiește URL direct
                        base_url = ou_link.split('#')[0]
                        direct_url = f"{base_url}#over-under;1;{line_val};0"
                        
                        # Navighează la URL-ul direct
                        print(f"  📡 Accesez URL pentru cote...")
                        driver.get(direct_url)
                        time.sleep(5)
                        
                        # Extrage cotele Betano
                        over_odd, under_odd = extract_betano_odds_comprehensive(driver)
                        
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
                        time.sleep(4)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare element OU {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP SCRAPING
        print("\n🔍 ASIAN HANDICAP - Încep extragerea...")
        try:
            driver.get(ah_link)
            time.sleep(8)
            
            ah_lines = []
            
            # Găsește toate liniile Asian Handicap
            ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
            print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
            
            processed_ah_lines = set()
            
            for i, element in enumerate(ah_elements[:8]):  # Limitează la primele 8
                try:
                    text = element.text.strip()
                    if 'Asian Handicap' in text and any(c in text for c in ['+', '-']):
                        # Extrage valoarea liniei
                        match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                        if match:
                            line_val = match.group(1)
                            
                            if line_val in processed_ah_lines:
                                continue
                            processed_ah_lines.add(line_val)
                            
                            print(f"  {i+1}. LINIE AH EXTRASĂ: {line_val}")
                            
                            # Construiește URL direct pentru AH
                            base_url = ah_link.split('#')[0]
                            clean_val = line_val.replace('+', '').replace('-', '')
                            direct_url = f"{base_url}#ah;1;{clean_val};0"
                            
                            # Navighează la URL-ul direct
                            print(f"  📡 Accesez URL pentru cote AH...")
                            driver.get(direct_url)
                            time.sleep(5)
                            
                            # Extrage cotele Betano (folosește aceeași funcție)
                            home_odd, away_odd = extract_betano_odds_comprehensive(driver)
                            
                            # Salvează rezultatul
                            ah_lines.append({
                                'Line': line_val,
                                'Home_Close': home_odd,
                                'Away_Close': away_odd,
                                'Bookmaker': 'Betano.ro',
                                'Direct_URL': direct_url
                            })
                            
                            # Revino la pagina principală AH
                            driver.get(ah_link)
                            time.sleep(4)
                            
                except Exception as e:
                    print(f"  ⚠️ Eroare element AH {i+1}: {e}")
                    continue
                    
            results['Handicap_Lines'] = ah_lines
        except Exception as e:
            print(f"⚠️ Eroare la scraping AH: {e}")
            results['Handicap_Lines'] = []
        
        # SALVARE REZULTATE
        results['Over_Under_Lines'] = ou_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(results['Handicap_Lines']),
            'unique_ou_lines': list(processed_lines),
            'unique_ah_lines': list(processed_ah_lines) if 'processed_ah_lines' in locals() else [],
            'strategy': 'Extracție Betano cu webdriver_manager',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLETAT!")
        print(f"📊 REZULTATE: {len(ou_lines)} linii OU, {len(results['Handicap_Lines'])} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
        import traceback
        print(f"🔍 DETALII EROARE: {traceback.format_exc()}")
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Browser închis")
    
    return results
