def scrape_via_direct_urls(ou_link, ah_link):
    import requests
    import re
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By  # IMPORT LIPSĂ
    import os
    import time
    
    results = {'Match': 'Scraping via URL-uri directe'}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
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
        
        # 1. CLICK PE TAB OVER/UNDER
        try:
            ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
            driver.execute_script("arguments[0].click();", ou_tab)
            print("✓ Click pe tab Over/Under")
            time.sleep(3)
        except Exception as e:
            print(f"✗ Tab Over/Under nu a putut fi apăsat: {e}")
        
        # 2. EXTRAGE TOATE VALORILE LINIILOR (metodă îmbunătățită)
        ou_lines = []
        line_values = []
        
        # Încearcă mai mulți selectorii pentru a găsi liniile
        selectors = [
            "//div[contains(@class, 'min-md:px-[10px]')]//div[contains(@class, 'font-bold')]",
            "//div[contains(text(), 'Over/Under')]",
            "//*[contains(text(), 'Over/Under')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements[:10]:
                    text = element.text.strip()
                    if "Over/Under" in text:
                        # Extrage valoarea liniei - mai robust
                        line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', text)
                        if line_match:
                            line_value = line_match.group(1)
                            # Asigură-te că valoarea este normalizată
                            clean_value = line_value.replace('+', '').replace('-', '')
                            if clean_value not in [lv.replace('+', '').replace('-', '') for lv in line_values]:
                                line_values.append(line_value)
                                print(f"✓ Linie găsită: {line_value}")
            except:
                continue
        
        print(f"Total valori linii extrase: {len(line_values)}: {line_values}")
        
        # 3. CONSTRUIEȘTE URL-URI DIRECTE PENTRU FIECARE LINIE
        base_url = ou_link.split('#')[0]
        
        for i, line_value in enumerate(line_values[:3]):
            try:
                # Construiește URL-ul direct pentru linie
                clean_line = line_value.replace('+', '').replace('-', '')
                direct_url = f"{base_url}#over-under;1;{clean_line};0"
                print(f"URL direct linie {i+1}: {direct_url}")
                
                # Accesează URL-ul direct
                driver.get(direct_url)
                time.sleep(5)
                
                # VERIFICĂ DACA BETANO APARE (metodă îmbunătățită)
                betano_selectors = [
                    "//*[contains(text(), 'Betano')]",
                    "//*[contains(text(), 'Betano.ro')]",
                    "//a[contains(@href, 'betano')]"
                ]
                
                betano_found = False
                for selector in betano_selectors:
                    try:
                        betano_elements = driver.find_elements(By.XPATH, selector)
                        if betano_elements:
                            betano_found = True
                            break
                    except:
                        continue
                
                print(f"  Elemente Betano după URL direct: {betano_found}")
                
                if betano_found:
                    print(f"  ✅ BETANO GĂSIT la linia {line_value}!")
                    
                    # EXTRAge COTELE (metodă mai robustă)
                    odds_data = {'over': 'N/A', 'under': 'N/A'}
                    
                    # Încearcă mai mulți selectorii pentru cote
                    odds_selectors = [
                        "//p[@class='odds-text']",
                        "//div[contains(@class, 'odds')]",
                        "//span[contains(@class, 'odds')]"
                    ]
                    
                    for selector in odds_selectors:
                        try:
                            odds_elements = driver.find_elements(By.XPATH, selector)
                            if len(odds_elements) >= 2:
                                odds_data['over'] = odds_elements[0].text
                                odds_data['under'] = odds_elements[1].text
                                break
                        except:
                            continue
                    
                    print(f"  ✅ Cote găsite: Over={odds_data['over']}, Under={odds_data['under']}")
                    
                    ou_lines.append({
                        'Line': line_value,
                        'Over_Close': odds_data['over'],
                        'Over_Open': 'N/A',
                        'Under_Close': odds_data['under'],
                        'Under_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                else:
                    print(f"  ❌ Betano nu a fost găsit pentru linia {line_value}")
                
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
        except Exception as e:
            print(f"✗ Tab Asian Handicap nu a putut fi apăsat: {e}")
        
        ah_lines = []
        ah_line_values = []
        
        # Extrage liniile AH
        ah_selectors = [
            "//div[contains(@class, 'min-md:px-[10px]')]//div[contains(@class, 'font-bold')]",
            "//div[contains(text(), 'Asian Handicap')]",
            "//*[contains(text(), 'Asian Handicap')]"
        ]
        
        for selector in ah_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements[:10]:
                    text = element.text.strip()
                    if "Asian Handicap" in text:
                        line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                        if line_match:
                            line_value = line_match.group(1)
                            clean_value = line_value.replace('+', '').replace('-', '')
                            if clean_value not in [lv.replace('+', '').replace('-', '') for lv in ah_line_values]:
                                ah_line_values.append(line_value)
                                print(f"✓ Linie AH găsită: {line_value}")
            except:
                continue
        
        # Construiește URL-uri pentru AH
        ah_base_url = ah_link.split('#')[0]
        
        for i, line_value in enumerate(ah_line_values[:3]):
            try:
                clean_line = line_value.replace('+', '').replace('-', '')
                direct_ah_url = f"{ah_base_url}#ah;1;{clean_line};0"
                print(f"URL direct AH linie {i+1}: {direct_ah_url}")
                
                driver.get(direct_ah_url)
                time.sleep(5)
                
                # Verifică Betano pentru AH
                betano_found_ah = False
                for selector in betano_selectors:
                    try:
                        betano_elements = driver.find_elements(By.XPATH, selector)
                        if betano_elements:
                            betano_found_ah = True
                            break
                    except:
                        continue
                
                print(f"  Elemente Betano AH: {betano_found_ah}")
                
                if betano_found_ah:
                    print(f"  ✅ BETANO GĂSIT la AH linia {line_value}!")
                    
                    odds_data_ah = {'home': 'N/A', 'away': 'N/A'}
                    
                    for selector in odds_selectors:
                        try:
                            odds_elements = driver.find_elements(By.XPATH, selector)
                            if len(odds_elements) >= 2:
                                odds_data_ah['home'] = odds_elements[0].text
                                odds_data_ah['away'] = odds_elements[1].text
                                break
                        except:
                            continue
                    
                    print(f"  ✅ Cote AH găsite: Home={odds_data_ah['home']}, Away={odds_data_ah['away']}")
                    
                    ah_lines.append({
                        'Line': line_value,
                        'Home_Close': odds_data_ah['home'],
                        'Home_Open': 'N/A',
                        'Away_Close': odds_data_ah['away'],
                        'Away_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_ah_url
                    })
                else:
                    print(f"  ❌ Betano nu a fost găsit pentru AH linia {line_value}")
                
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
        import traceback
        results['Traceback'] = traceback.format_exc()
    finally:
        if 'driver' in locals():
            driver.quit()
    
    return results

# Funcția principală
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_via_direct_urls(ou_link, ah_link)
