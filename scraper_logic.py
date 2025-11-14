def scrape_via_direct_urls(ou_link, ah_link):
    import requests
    import re
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import os
    import time
    
    results = {'Match': 'Scraping via URL-uri directe'}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # ----------------------------------------------------
        # OVER/UNDER - EXTRAGEM LINIILE ȘI CONSTRUIM URL-URI
        # ----------------------------------------------------
        print("=== OVER/UNDER - URL-URI DIRECTE ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER (doar pentru a vedea liniile)
        try:
            ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
            driver.execute_script("arguments[0].click();", ou_tab)
            print("✓ Click pe tab Over/Under")
            time.sleep(3)
        except:
            print("✗ Tab Over/Under nu a putut fi apăsat")
        
        # 2. EXTRAGE TOATE VALORILE LINIILOR
        ou_lines = []
        line_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'min-md:px-[10px]')]/div")
        print(f"Containere linii găsite: {len(line_containers)}")
        
        line_values = []
        for container in line_containers[:10]:  # Primele 10 linii
            try:
                text_elements = container.find_elements(By.XPATH, ".//div[contains(@class, 'font-bold text-[#2F2F2F]')]")
                if not text_elements:
                    continue
                    
                line_text = text_elements[0].text
                if "Over/Under" in line_text:
                    # Extrage valoarea liniei (ex: +218.5)
                    line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                    if line_match:
                        line_value = line_match.group(1)
                        line_values.append(line_value)
                        print(f"✓ Linie găsită: {line_value}")
            except:
                continue
        
        print(f"Total valori linii extrase: {len(line_values)}")
        
        # 3. CONSTRUIEȘTE URL-URI DIRECTE PENTRU FIECARE LINIE
        base_url = ou_link.split('#')[0]  # https://www.oddsportal.com/basketball/usa/nba/cleveland-cavaliers-toronto-raptors-xYgsQpLr/
        
        for i, line_value in enumerate(line_values[:3]):  # Testează primele 3 linii
            try:
                # Construiește URL-ul direct pentru linie
                # Format: #over-under;1;218.50;0
                direct_url = f"{base_url}#over-under;1;{line_value.replace('+', '').replace('-', '')};0"
                print(f"URL direct linie {i+1}: {direct_url}")
                
                # Accesează URL-ul direct
                driver.get(direct_url)
                time.sleep(5)
                
                # VERIFICĂ DACA BETANO APARE
                betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano.ro')]")
                print(f"  Elemente Betano după URL direct: {len(betano_elements)}")
                
                if betano_elements:
                    print(f"  ✅ BETANO GĂSIT la linia {line_value}!")
                    
                    # EXTRAge COTELE
                    odds_elements = driver.find_elements(By.XPATH, "//p[@class='odds-text']")
                    if len(odds_elements) >= 2:
                        over_close = odds_elements[0].text
                        under_close = odds_elements[1].text
                        
                        print(f"  ✅ Cote găsite: Over={over_close}, Under={under_close}")
                        
                        ou_lines.append({
                            'Line': line_value,
                            'Over_Close': over_close,
                            'Over_Open': 'N/A',
                            'Under_Close': under_close,
                            'Under_Open': 'N/A',
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_url
                        })
                
            except Exception as e:
                print(f"✗ Eroare la linia {line_value}: {e}")
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEAȘI LOGICĂ
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP - URL-URI DIRECTE ===")
        driver.get(ah_link)
        time.sleep(5)
        
        try:
            ah_tab = driver.find_element(By.XPATH, "//div[text()='Asian Handicap']")
            driver.execute_script("arguments[0].click();", ah_tab)
            print("✓ Click pe tab Asian Handicap")
            time.sleep(3)
        except:
            print("✗ Tab Asian Handicap nu a putut fi apăsat")
        
        ah_lines = []
        ah_line_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'min-md:px-[10px]')]/div")
        
        ah_line_values = []
        for container in ah_line_containers[:10]:
            try:
                text_elements = container.find_elements(By.XPATH, ".//div[contains(@class, 'font-bold text-[#2F2F2F]')]")
                if not text_elements:
                    continue
                    
                line_text = text_elements[0].text
                if "Asian Handicap" in line_text:
                    line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                    if line_match:
                        line_value = line_match.group(1)
                        ah_line_values.append(line_value)
                        print(f"✓ Linie AH găsită: {line_value}")
            except:
                continue
        
        # Construiește URL-uri pentru AH
        ah_base_url = ah_link.split('#')[0]
        
        for i, line_value in enumerate(ah_line_values[:3]):
            try:
                # Format pentru AH: #ah;1;-5.50;0
                direct_ah_url = f"{ah_base_url}#ah;1;{line_value.replace('+', '').replace('-', '')};0"
                print(f"URL direct AH linie {i+1}: {direct_ah_url}")
                
                driver.get(direct_ah_url)
                time.sleep(5)
                
                betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano.ro')]")
                print(f"  Elemente Betano AH: {len(betano_elements)}")
                
                if betano_elements:
                    print(f"  ✅ BETANO GĂSIT la AH linia {line_value}!")
                    
                    odds_elements = driver.find_elements(By.XPATH, "//p[@class='odds-text']")
                    if len(odds_elements) >= 2:
                        home_close = odds_elements[0].text
                        away_close = odds_elements[1].text
                        
                        print(f"  ✅ Cote AH găsite: Home={home_close}, Away={away_close}")
                        
                        ah_lines.append({
                            'Line': line_value,
                            'Home_Close': home_close,
                            'Home_Open': 'N/A',
                            'Away_Close': away_close,
                            'Away_Open': 'N/A',
                            'Bookmaker': 'Betano.ro',
                            'Direct_URL': direct_ah_url
                        })
                
            except Exception as e:
                print(f"✗ Eroare la AH linia {line_value}: {e}")
        
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'ou_line_values': line_values[:5],
            'ah_line_values': ah_line_values[:5]
        }
        
    except Exception as e:
        results['Error'] = f"Eroare URL-uri directe: {str(e)}"
    finally:
        if 'driver' in locals():
            driver.quit()
    
    return results

# FOLOSEȘTE ACEST COD! 
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_via_direct_urls(ou_link, ah_link)
