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

def extract_betano_odds_fixed(driver):
    """Extrage cotele Betano folosind structura corectă din HTML"""
    over_odd, under_odd = 'N/A', 'N/A'
    
    try:
        # METODA 1: Caută direct după logo-ul Betano
        betano_logos = driver.find_elements(By.XPATH, "//img[contains(@src, 'betano') or contains(@alt, 'Betano') or contains(@title, 'Betano')]")
        print(f"    🔍 Logo-uri Betano găsite: {len(betano_logos)}")
        
        for logo in betano_logos:
            try:
                # Găsește rândul părinte care conține logo-ul Betano
                row = logo.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                
                # Extrage cotele din acest rând
                odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                
                if len(odds_elements) >= 2:
                    over_odd = odds_elements[0].text.strip()
                    under_odd = odds_elements[1].text.strip()
                    print(f"    ✅ COTE BETANO EXTRASE: Over={over_odd}, Under={under_odd}")
                    return over_odd, under_odd
                    
            except Exception as e:
                continue
        
        # METODA 2: Caută după numele Betano în text
        betano_text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano') or contains(text(), 'betano')]")
        print(f"    🔍 Elemente text Betano găsite: {len(betano_text_elements)}")
        
        for element in betano_text_elements:
            try:
                row = element.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                
                if len(odds_elements) >= 2:
                    over_odd = odds_elements[0].text.strip()
                    under_odd = odds_elements[1].text.strip()
                    print(f"    ✅ COTE BETANO (metoda text): Over={over_odd}, Under={under_odd}")
                    return over_odd, under_odd
                    
            except Exception as e:
                continue
                
        # METODA 3: Caută în toate rândurile expandate
        expanded_rows = driver.find_elements(By.XPATH, "//div[contains(@data-testid, 'over-under-expanded-row')]")
        print(f"    🔍 Rânduri expandate găsite: {len(expanded_rows)}")
        
        for row in expanded_rows:
            try:
                # Verifică dacă rândul conține Betano
                row_html = row.get_attribute('innerHTML')
                if 'betano' in row_html.lower():
                    odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                    
                    if len(odds_elements) >= 2:
                        over_odd = odds_elements[0].text.strip()
                        under_odd = odds_elements[1].text.strip()
                        print(f"    ✅ COTE BETANO (metoda rând): Over={over_odd}, Under={under_odd}")
                        return over_odd, under_odd
                        
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"    ⚠️ Eroare la extragerea cotelor Betano: {e}")
    
    return over_odd, under_odd

def extract_ah_betano_odds_fixed(driver):
    """Extrage cotele Betano pentru Asian Handicap"""
    home_odd, away_odd = 'N/A', 'N/A'
    
    try:
        # Aceeași logică ca pentru Over/Under
        betano_logos = driver.find_elements(By.XPATH, "//img[contains(@src, 'betano') or contains(@alt, 'Betano') or contains(@title, 'Betano')]")
        print(f"    🔍 Logo-uri Betano AH găsite: {len(betano_logos)}")
        
        for logo in betano_logos:
            try:
                row = logo.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                
                if len(odds_elements) >= 2:
                    home_odd = odds_elements[0].text.strip()
                    away_odd = odds_elements[1].text.strip()
                    print(f"    ✅ COTE AH BETANO: Home={home_odd}, Away={away_odd}")
                    return home_odd, away_odd
                    
            except Exception as e:
                continue
                
        # Metoda alternativă pentru AH
        betano_text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano')]")
        
        for element in betano_text_elements:
            try:
                row = element.find_element(By.XPATH, "./ancestor::div[contains(@data-testid, 'over-under-expanded-row')]")
                odds_elements = row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                
                if len(odds_elements) >= 2:
                    home_odd = odds_elements[0].text.strip()
                    away_odd = odds_elements[1].text.strip()
                    print(f"    ✅ COTE AH BETANO (text): Home={home_odd}, Away={away_odd}")
                    return home_odd, away_odd
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"    ⚠️ Eroare la extragerea cotelor AH Betano: {e}")
    
    return home_odd, away_odd

def scrape_basketball_match_fixed(ou_link, ah_link):
    """
    SCRAPING ÎMBUNĂTĂȚIT CU EXTRAGERE CORECTĂ A COTELOR BETANO
    """
    
    results = {
        'Match': 'Scraping Îmbunătățit Betano',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING ÎMBUNĂTĂȚIT BETANO ===")
        
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
        
        # Setări specifice pentru Streamlit Cloud
        options.binary_location = "/usr/bin/chromium"
        
        try:
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
        except:
            # Fallback dacă chromedriver nu este în path-ul așteptat
            driver = webdriver.Chrome(options=options)
        
        # Ascunde automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Browser pornit cu succes!")
        
        # OVER/UNDER SCRAPING
        print("🔍 OVER/UNDER - Încep extragerea...")
        driver.get(ou_link)
        
        # Așteaptă încărcarea paginii
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(8)
        
        ou_lines = []
        
        # Găsește toate liniile Over/Under
        ou_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        print(f"📊 Elemente Over/Under găsite: {len(ou_elements)}")
        
        processed_lines = set()
        
        for i, element in enumerate(ou_elements[:12]):  # Limitează la primele 12
            try:
                text = element.text.strip()
                if 'Over/Under' in text:
                    # Extrage valoarea liniei
                    match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        
                        # Evită duplicate
                        if line_val in processed_lines:
                            continue
                        processed_lines.add(line_val)
                        
                        display_line = f"+{line_val}"
                        print(f"  ✅ LINIE OU EXTRASĂ: {display_line}")
                        
                        # Construiește URL direct pentru linia respectivă
                        base_url = ou_link.split('#')[0]
                        direct_url = f"{base_url}#over-under;1;{line_val};0"
                        
                        # Navighează la URL-ul direct pentru cote
                        print(f"  📡 Accesez URL pentru cote OU...")
                        driver.get(direct_url)
                        time.sleep(6)
                        
                        # Extrage cotele Betano folosind funcția fixată
                        over_odd, under_odd = extract_betano_odds_fixed(driver)
                        
                        # Salvează rezultatul
                        ou_lines.append({
                            'Line': display_line,
                            'Over_Close': over_odd,
                            'Under_Close': under_odd,
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                        
                        # Revino la pagina principală OU
                        driver.get(ou_link)
                        time.sleep(5)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare element OU {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP SCRAPING
        print("\n🔍 ASIAN HANDICAP - Încep extragerea...")
        driver.get(ah_link)
        time.sleep(8)
        
        ah_lines = []
        
        # Găsește toate liniile Asian Handicap
        ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
        
        processed_ah_lines = set()
        
        for i, element in enumerate(ah_elements[:10]):  # Limitează la primele 10
            try:
                text = element.text.strip()
                if 'Asian Handicap' in text:
                    # Extrage valoarea liniei
                    match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        
                        # Evită duplicate
                        if line_val in processed_ah_lines:
                            continue
                        processed_ah_lines.add(line_val)
                        
                        print(f"  ✅ LINIE AH EXTRASĂ: {line_val}")
                        
                        # Construiește URL direct pentru Asian Handicap
                        base_url = ah_link.split('#')[0]
                        clean_val = line_val.replace('+', '').replace('-', '')
                        direct_url = f"{base_url}#ah;1;{clean_val};0"
                        
                        # Navighează la URL-ul direct pentru cote AH
                        print(f"  📡 Accesez URL pentru cote AH...")
                        driver.get(direct_url)
                        time.sleep(6)
                        
                        # Extrage cotele Betano pentru AH
                        home_odd, away_odd = extract_ah_betano_odds_fixed(driver)
                        
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
                        time.sleep(5)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare element AH {i+1}: {e}")
                continue
        
        # SALVARE REZULTATE
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'unique_ou_lines': list(processed_lines),
            'unique_ah_lines': list(processed_ah_lines),
            'strategy': 'Extracție Betano cu structură fixă',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLETAT CU SUCCES!")
        print(f"📊 REZULTATE: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
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

# Funcție simplificată pentru testare rapidă
def scrape_betano_odds_simple(url):
    """Scrape rapid doar pentru Betano de pe o pagină specifică"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except:
        driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(8)
        over_odd, under_odd = extract_betano_odds_fixed(driver)
        return {'over': over_odd, 'under': under_odd}
    finally:
        driver.quit()
