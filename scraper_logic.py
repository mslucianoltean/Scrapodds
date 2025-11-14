def scrape_correct_flow(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    
    results = {'Match': 'Scraping cu flow corect'}
    driver = None
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        
        # ----------------------------------------------------
        # OVER/UNDER
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(3)
        
        # 1. CLICK PE TAB OVER/UNDER
        try:
            ou_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Over/Under')]")))
            driver.execute_script("arguments[0].click();", ou_tab)
            print("✓ Click tab Over/Under")
            time.sleep(2)
        except Exception as e:
            print(f"✗ Eroare tab OU: {e}")
            results['OU_Error'] = f"Tab not found: {e}"
        
        # 2. GĂSEȘTE TOATE LINIILE
        ou_lines = []
        try:
            # Selector pentru liniile care pot fi expandate
            line_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'table-main') or contains(@class, 'line') or contains(@class, 'option')]")
            print(f"Găsite {len(line_elements)} linii potențiale")
            
            for i, line_element in enumerate(line_elements[:10]):  # Testează primele 10
                try:
                    print(f"Încerc linia {i+1}")
                    
                    # Click pe linie pentru a expanda bookmakerii
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1.5)
                    
                    # 3. CAUTĂ BETANO ÎN BOOKMAKERI
                    betano_selectors = [
                        "//a[contains(@href, 'betano')]",
                        "//*[contains(text(), 'Betano')]",
                        "//*[contains(text(), 'BETANO')]"
                    ]
                    
                    betano_found = False
                    for selector in betano_selectors:
                        try:
                            betano_elements = driver.find_elements(By.XPATH, selector)
                            if betano_elements:
                                betano_parent = betano_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or contains(@class, 'bookmaker')][1]")
                                
                                # 4. EXTRAge COTELE de lângă Betano
                                odds_elements = betano_parent.find_elements(By.XPATH, ".//*[contains(@class, 'odds') or contains(@class, 'price') or contains(text(), '.')]")
                                
                                if len(odds_elements) >= 2:
                                    over_close = odds_elements[0].text
                                    under_close = odds_elements[1].text
                                    
                                    # 5. EXTRAge OPENING ODDS (dă click pe cote)
                                    over_open = get_opening_odds(driver, odds_elements[0])
                                    under_open = get_opening_odds(driver, odds_elements[1])
                                    
                                    # 6. EXTRAge LINIA (textul liniei expandate)
                                    line_text = line_element.text
                                    line_value = extract_line_value(line_text)
                                    
                                    ou_lines.append({
                                        'Line': line_value,
                                        'Home_Over_Close': over_close,
                                        'Home_Over_Open': over_open,
                                        'Away_Under_Close': under_close,
                                        'Away_Under_Open': under_open,
                                        'Bookmaker': 'Betano'
                                    })
                                    
                                    print(f"✓ Găsit Betano la linia: {line_value}")
                                    betano_found = True
                                    break
                                    
                        except Exception as e:
                            continue
                    
                    if betano_found:
                        break  # Am găsit Betano, trecem la următorul
                        
                    # Colapsează linia pentru următoarea
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Eroare la linia {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Eroare generală OU: {e}")
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP (același flow)
        # ----------------------------------------------------
        print("=== START ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(3)
        
        # Repetă același flow pentru Asian Handicap...
        # (cod similar pentru AH)
        
        results['Handicap_Lines'] = []  # Temporar
        
    except Exception as e:
        results['Error'] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds(driver, odds_element):
    """Dă click pe o cotă și extrage opening odds din popup"""
    try:
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(1)
        
        # Caută opening odds în popup
        popup_selectors = [
            "//*[contains(text(), 'Opening odds')]",
            "//*[contains(@class, 'tooltip')]",
            "//*[contains(@class, 'popup')]"
        ]
        
        for selector in popup_selectors:
            try:
                popup_element = driver.find_element(By.XPATH, selector)
                popup_text = popup_element.text
                # Extrage numărul
                import re
                match = re.search(r'(\d+\.\d+)', popup_text)
                if match:
                    return match.group(1)
            except:
                continue
        
        return 'N/A'
        
    except:
        return 'N/A'

def extract_line_value(text):
    """Extrage valoarea liniei din text"""
    import re
    matches = re.findall(r'[+-]?\d+\.?\d*', text)
    return matches[0] if matches else 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_correct_flow(ou_link, ah_link)
