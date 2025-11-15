import requests
from bs4 import BeautifulSoup
import re
import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING CU UNDETECTED CHROMEDRIVER - Soluția care merge
    """
    
    results = {
        'Match': 'Scraping cu Browser Real',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    driver = None
    
    try:
        print("=== ÎNCEPE SCRAPING CU BROWSER REAL ===")
        
        # Configurare browser stealth
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Folosește undetected-chromedriver pentru a evita detectarea
        driver = uc.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # OVER/UNDER
        print("🔍 Accesez pagina Over/Under...")
        driver.get(ou_link)
        
        # Așteaptă să se încarce conținutul
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Așteaptă puțin pentru JS
        time.sleep(5)
        
        # Salvează HTML-ul pentru debug
        html_content = driver.page_source
        print(f"📄 Lungime HTML: {len(html_content)} caractere")
        
        # Parsează cu BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # DEBUG: Afișează tot HTML-ul pentru a vedea ce conține
        print("🔍 Caut elemente în HTML...")
        
        # Verifică dacă vedem ceva util
        all_text = soup.get_text()
        if 'Over/Under' in all_text:
            print("✅ 'Over/Under' găsit în textul paginii!")
        else:
            print("❌ 'Over/Under' NU găsit în text")
        
        # Caută liniile Over/Under în mai multe moduri
        ou_lines = []
        
        # Încearcă multiple selectori
        selectors = [
            "//p[contains(text(), 'Over/Under')]",
            "//div[contains(text(), 'Over/Under')]",
            "//*[contains(text(), 'Over/Under')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"🔍 Selector '{selector}': {len(elements)} elemente")
                
                for element in elements[:5]:
                    try:
                        text = element.text.strip()
                        print(f"  📝 Text găsit: {text}")
                        
                        match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                        if match:
                            line_val = match.group(1)
                            display_line = f"+{line_val}"
                            print(f"  ✅ LINIE EXTRASĂ: {display_line}")
                            
                            # Construiește URL direct
                            base_url = ou_link.split('#')[0]
                            direct_url = f"{base_url}#over-under;1;{line_val};0"
                            
                            # Navighează la URL-ul direct pentru a găsi Betano
                            driver.get(direct_url)
                            time.sleep(3)
                            
                            # Caută Betano pe pagina cu linia specifică
                            betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                            print(f"  🔍 Elemente Betano găsite: {len(betano_elements)}")
                            
                            over_odd, under_odd = 'N/A', 'N/A'
                            
                            if betano_elements:
                                # Găsește rândul Betano
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                                
                                if len(odds_elements) >= 2:
                                    over_odd = odds_elements[0].text.strip()
                                    under_odd = odds_elements[1].text.strip()
                                    print(f"  ✅ COTE GĂSITE: Over={over_odd}, Under={under_odd}")
                            
                            ou_lines.append({
                                'Line': display_line,
                                'Over_Close': over_odd,
                                'Under_Close': under_odd,
                                'Bookmaker': 'Betano.ro',
                                'Direct_URL': direct_url
                            })
                            
                            # Revino la pagina principală
                            driver.get(ou_link)
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"  ⚠️ Eroare procesare element: {e}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Eroare selector {selector}: {e}")
        
        # ASIAN HANDICAP (același proces)
        print("\n🔍 Accesez pagina Asian Handicap...")
        driver.get(ah_link)
        time.sleep(5)
        
        ah_lines = []
        
        ah_selectors = [
            "//p[contains(text(), 'Asian Handicap')]",
            "//div[contains(text(), 'Asian Handicap')]", 
            "//*[contains(text(), 'Asian Handicap')]"
        ]
        
        for selector in ah_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"🔍 Selector AH '{selector}': {len(elements)} elemente")
                
                for element in elements[:3]:
                    try:
                        text = element.text.strip()
                        print(f"  📝 Text AH găsit: {text}")
                        
                        match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                        if match:
                            line_val = match.group(1)
                            clean_val = line_val.replace('+', '').replace('-', '')
                            print(f"  ✅ LINIE AH EXTRASĂ: {line_val}")
                            
                            base_url = ah_link.split('#')[0]
                            direct_url = f"{base_url}#ah;1;{clean_val};0"
                            
                            # Navighează la URL-ul AH direct
                            driver.get(direct_url)
                            time.sleep(3)
                            
                            # Caută Betano pentru AH
                            betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                            print(f"  🔍 Elemente Betano AH găsite: {len(betano_elements)}")
                            
                            home_odd, away_odd = 'N/A', 'N/A'
                            
                            if betano_elements:
                                betano_row = betano_elements[0].find_element(By.XPATH, "./../..")
                                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'odds-text')]")
                                
                                if len(odds_elements) >= 2:
                                    home_odd = odds_elements[0].text.strip()
                                    away_odd = odds_elements[1].text.strip()
                                    print(f"  ✅ COTE AH GĂSITE: Home={home_odd}, Away={away_odd}")
                            
                            ah_lines.append({
                                'Line': line_val,
                                'Home_Close': home_odd,
                                'Away_Close': away_odd,
                                'Bookmaker': 'Betano.ro', 
                                'Direct_URL': direct_url
                            })
                            
                            driver.get(ah_link)
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"  ⚠️ Eroare procesare AH element: {e}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Eroare selector AH {selector}: {e}")
        
        # Salvează rezultatele
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'strategy': 'Undetected ChromeDriver',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ FINAL: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    finally:
        if driver:
            driver.quit()
    
    return results
