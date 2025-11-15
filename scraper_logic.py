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
    SCRAPING CU CHROMIUM DIRECT - Compatibil cu Streamlit Cloud
    """
    
    results = {
        'Match': 'Scraping cu Chromium',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING CU CHROMIUM ===")
        
        # Configurare pentru Streamlit Cloud
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Folosește Chromium din sistem (pre-instalat pe Streamlit Cloud)
        options.binary_location = "/usr/bin/chromium"
        
        # Setează ChromeDriver path pentru Chromium
        chromedriver_path = "/usr/bin/chromedriver"
        
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Fallback - folosește Chromium direct
            driver = webdriver.Chrome(options=options)
        
        # Ascunde automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Browser pornit cu succes!")
        
        # OVER/UNDER
        print("🔍 Accesez pagina Over/Under...")
        driver.get(ou_link)
        
        # Așteaptă mai mult pentru cloud
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        time.sleep(10)  # Așteaptă generos pentru JS
        
        # Verifică conținutul paginii
        html_content = driver.page_source
        print(f"📄 Lungime HTML: {len(html_content)} caractere")
        
        # DEBUG: Salvează prima pagină pentru analiză
        with open('debug_page1.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("💾 Pagina 1 salvată pentru debug")
        
        # Verifică dacă vedem ceva util
        if 'Over/Under' in html_content:
            print("✅ 'Over/Under' găsit în HTML!")
        else:
            print("❌ 'Over/Under' NU găsit în HTML")
            # Afișează o porțiune din HTML pentru debug
            print("📝 Fragment HTML:", html_content[:500])
        
        # ÎNCEARCĂ MULTIPLE STRATEGII DE EXTRAGERE
        
        ou_lines = []
        
        # STRATEGIA 1: Caută prin toate elementele care conțin text
        print("\n🔍 STRATEGIA 1 - Caut în toate elementele...")
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        print(f"📊 Elemente cu 'Over/Under' găsite: {len(all_elements)}")
        
        for i, element in enumerate(all_elements[:15]):
            try:
                text = element.text.strip()
                if text and 'Over/Under' in text:
                    print(f"  {i+1}. {text}")
                    
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
                        print(f"  📡 Accesez URL direct...")
                        driver.get(direct_url)
                        time.sleep(8)  # Așteaptă generos
                        
                        # Salvează pagina cu linia specifică pentru debug
                        with open(f'debug_line_{line_val}.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        
                        # Caută Betano
                        betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                        print(f"  🔍 Elemente Betano găsite: {len(betano_elements)}")
                        
                        over_odd, under_odd = 'N/A', 'N/A'
                        
                        if betano_elements:
                            try:
                                # Găsește rândul Betano
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                
                                # Caută cotele
                                odds_selectors = [
                                    ".//p[contains(@class, 'odds-text')]",
                                    ".//span[contains(@class, 'odds')]",
                                    ".//div[contains(@class, 'odds')]"
                                ]
                                
                                for selector in odds_selectors:
                                    odds_elements = betano_row.find_elements(By.XPATH, selector)
                                    if len(odds_elements) >= 2:
                                        over_odd = odds_elements[0].text.strip()
                                        under_odd = odds_elements[1].text.strip()
                                        print(f"  ✅ COTE: Over={over_odd}, Under={under_odd}")
                                        break
                                        
                            except Exception as e:
                                print(f"  ⚠️ Eroare extragere cote: {e}")
                        
                        # Salvează linia
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
        
        # Dacă nu am găsit nimic, încercă o strategie alternativă
        if not ou_lines:
            print("\n🔍 STRATEGIA 2 - Caut în innerHTML...")
            # Obține tot HTML-ul și parsează cu BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            all_text = soup.get_text()
            
            # Caută pattern-uri de linii în tot textul
            line_patterns = re.findall(r'Over/Under\s*\+?(\d+\.?\d*)', all_text)
            unique_lines = list(set(line_patterns))
            
            print(f"📊 Linii găsite în text: {unique_lines}")
            
            for line_val in unique_lines[:3]:
                try:
                    display_line = f"+{line_val}"
                    base_url = ou_link.split('#')[0]
                    direct_url = f"{base_url}#over-under;1;{line_val};0"
                    
                    print(f"🎯 Procesez linia din text: {display_line}")
                    
                    driver.get(direct_url)
                    time.sleep(8)
                    
                    betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                    print(f"🔍 Betano elements: {len(betano_elements)}")
                    
                    over_odd, under_odd = 'N/A', 'N/A'
                    
                    if betano_elements:
                        try:
                            betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                            odds_elements = betano_row.find_elements(By.XPATH, ".//p | .//span | .//div")
                            
                            # Filtrează elementele care ar putea fi cote
                            potential_odds = [elem for elem in odds_elements if elem.text.strip() and any(c.isdigit() or c == '.' for c in elem.text)]
                            
                            if len(potential_odds) >= 2:
                                over_odd = potential_odds[0].text.strip()
                                under_odd = potential_odds[1].text.strip()
                                print(f"✅ COTE TEXT: Over={over_odd}, Under={under_odd}")
                                
                        except Exception as e:
                            print(f"⚠️ Eroare cote text: {e}")
                    
                    ou_lines.append({
                        'Line': display_line,
                        'Over_Close': over_odd,
                        'Under_Close': under_odd,
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                    
                    driver.get(ou_link)
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"⚠️ Eroare procesare linie text: {e}")
                    continue
        
        # ASIAN HANDICAP (același proces)
        print("\n🔍 ASIAN HANDICAP - Încep extragerea...")
        driver.get(ah_link)
        time.sleep(10)
        
        ah_lines = []
        
        ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        print(f"📊 Elemente AH găsite: {len(ah_elements)}")
        
        for i, element in enumerate(ah_elements[:10]):
            try:
                text = element.text.strip()
                if text and 'Asian Handicap' in text:
                    print(f"  {i+1}. {text}")
                    
                    match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        clean_val = line_val.replace('+', '').replace('-', '')
                        print(f"  ✅ LINIE AH: {line_val}")
                        
                        base_url = ah_link.split('#')[0]
                        direct_url = f"{base_url}#ah;1;{clean_val};0"
                        
                        driver.get(direct_url)
                        time.sleep(8)
                        
                        betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                        print(f"  🔍 Betano AH: {len(betano_elements)}")
                        
                        home_odd, away_odd = 'N/A', 'N/A'
                        
                        if betano_elements:
                            try:
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                odds_elements = betano_row.find_elements(By.XPATH, ".//p | .//span | .//div")
                                potential_odds = [elem for elem in odds_elements if elem.text.strip() and any(c.isdigit() or c == '.' for c in elem.text)]
                                
                                if len(potential_odds) >= 2:
                                    home_odd = potential_odds[0].text.strip()
                                    away_odd = potential_odds[1].text.strip()
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
                        time.sleep(5)
                        
            except Exception as e:
                print(f"  ⚠️ Eroare AH {i+1}: {e}")
                continue
        
        # REZULTATE FINALE
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'total_ou_elements': len(all_elements),
            'total_ah_elements': len(ah_elements),
            'strategy': 'Chromium Direct + Multiple Approaches',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLET: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("🔚 Browser închis")
    
    return results
