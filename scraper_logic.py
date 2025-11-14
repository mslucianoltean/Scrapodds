def scrape_exact_betano(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu selector exact Betano'}
    driver = None
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # ----------------------------------------------------
        # OVER/UNDER - SELECTOR EXACT BETANO
        # ----------------------------------------------------
        print("=== OVER/UNDER CU SELECTOR EXACT ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        for tab in ou_tabs:
            if tab.text == "Over/Under":
                driver.execute_script("arguments[0].click();", tab)
                print("✓ Click pe tab Over/Under")
                time.sleep(3)
                break
        
        # 2. GĂSEȘTE TOATE LINIILE
        ou_lines = []
        line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under +') or contains(text(), 'Over/Under -')]")
        print(f"Găsite {len(line_elements)} linii OU")
        
        for i, line_element in enumerate(line_elements):
            try:
                line_text = line_element.text
                print(f"Procesez linia OU {i+1}: {line_text}")
                
                # Extrage valoarea liniei
                line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # 3. SELECTOR EXACT PENTRU BETANO - după href="betano.ro"
                betano_selectors = [
                    "//a[contains(@href, 'betano.ro')]",
                    "//a[contains(@href, 'betano.com')]",
                    "//a[contains(@href, 'betano')]"
                ]
                
                betano_link = None
                for selector in betano_selectors:
                    try:
                        betano_link = driver.find_element(By.XPATH, selector)
                        print(f"✓ Găsit Betano cu selector: {selector}")
                        break
                    except:
                        continue
                
                if not betano_link:
                    print("✗ Nicio variantă Betano nu a fost găsită")
                    # Click back și continuă
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                    continue
                
                # 4. GĂSEȘTE PĂRINTELE BETANO (rândul complet)
                betano_row = betano_link.find_element(By.XPATH, "./ancestor::div[1]")
                
                # 5. EXTRAge COTELE DIN RÂNDUL BETANO
                # Căutăm toate elementele cu cote (numere cu .) în rândul Betano
                all_text_elements = betano_row.find_elements(By.XPATH, ".//*")
                odds = []
                
                for elem in all_text_elements:
                    text = elem.text.strip()
                    if text and re.match(r'^\d+\.\d+$', text):  # Doar numere cu punct
                        odds.append(text)
                        if len(odds) >= 2:
                            break
                
                if len(odds) >= 2:
                    over_close = odds[0]
                    under_close = odds[1]
                    
                    # 6. GĂSEȘTE ELEMENTELE PENTRU CLICK (cele care afișează cotele)
                    click_elements = []
                    for elem in all_text_elements:
                        text = elem.text.strip()
                        if text in [over_close, under_close]:
                            click_elements.append(elem)
                            if len(click_elements) >= 2:
                                break
                    
                    # 7. EXTRAge OPENING ODDS
                    over_open = get_opening_odds_exact(driver, click_elements[0]) if len(click_elements) > 0 else 'N/A'
                    under_open = get_opening_odds_exact(driver, click_elements[1]) if len(click_elements) > 1 else 'N/A'
                    
                    ou_lines.append({
                        'Line': line_value,
                        'Over_Close': over_close,
                        'Over_Open': over_open,
                        'Under_Close': under_close,
                        'Under_Open': under_open,
                        'Bookmaker': 'Betano'
                    })
                    
                    print(f"✓ LINIE COMPLETĂ: {line_value} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                    break  # Am găsit Betano, ieșim
                
                # Click back
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"Eroare la linia OU {i+1}: {e}")
                # Încearcă să dai click back
                try:
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                except:
                    pass
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEAȘI LOGICĂ
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP CU SELECTOR EXACT ===")
        driver.get(ah_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB ASIAN HANDICAP
        ah_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        for tab in ah_tabs:
            if "Asian Handicap" in tab.text:
                driver.execute_script("arguments[0].click();", tab)
                print("✓ Click pe tab Asian Handicap")
                time.sleep(3)
                break
        
        # 2. GĂSEȘTE LINIILE ASIAN HANDICAP
        ah_lines = []
        ah_line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap +') or contains(text(), 'Asian Handicap -')]")
        print(f"Găsite {len(ah_line_elements)} linii AH")
        
        for i, line_element in enumerate(ah_line_elements):
            try:
                line_text = line_element.text
                print(f"Procesez linia AH {i+1}: {line_text}")
                
                line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # 3. GĂSEȘTE BETANO
                betano_link = None
                for selector in betano_selectors:
                    try:
                        betano_link = driver.find_element(By.XPATH, selector)
                        print(f"✓ Găsit Betano AH cu selector: {selector}")
                        break
                    except:
                        continue
                
                if not betano_link:
                    print("✗ Betano nu găsit pentru AH")
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                    continue
                
                # 4. EXTRAge COTELE
                betano_row = betano_link.find_element(By.XPATH, "./ancestor::div[1]")
                all_text_elements = betano_row.find_elements(By.XPATH, ".//*")
                odds = []
                
                for elem in all_text_elements:
                    text = elem.text.strip()
                    if text and re.match(r'^\d+\.\d+$', text):
                        odds.append(text)
                        if len(odds) >= 2:
                            break
                
                if len(odds) >= 2:
                    home_close = odds[0]
                    away_close = odds[1]
                    
                    click_elements = []
                    for elem in all_text_elements:
                        text = elem.text.strip()
                        if text in [home_close, away_close]:
                            click_elements.append(elem)
                            if len(click_elements) >= 2:
                                break
                    
                    home_open = get_opening_odds_exact(driver, click_elements[0]) if len(click_elements) > 0 else 'N/A'
                    away_open = get_opening_odds_exact(driver, click_elements[1]) if len(click_elements) > 1 else 'N/A'
                    
                    ah_lines.append({
                        'Line': line_value,
                        'Home_Close': home_close,
                        'Home_Open': home_open,
                        'Away_Close': away_close,
                        'Away_Open': away_open,
                        'Bookmaker': 'Betano'
                    })
                    
                    print(f"✓ LINIE AH COMPLETĂ: {line_value} | Home: {home_close}/{home_open} | Away: {away_close}/{away_open}")
                    break
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"Eroare la linia AH {i+1}: {e}")
                try:
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                except:
                    pass
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds_exact(driver, odds_element):
    """Extrage opening odds din popup"""
    try:
        original_odd = odds_element.text
        print(f"Click pentru opening odd pe: {original_odd}")
        
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(2)
        
        opening_odd = 'N/A'
        
        # Caută în tot documentul numere care arată a cote
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '.')]")
        for elem in all_elements:
            text = elem.text.strip()
            if text and text != original_odd and re.match(r'^\d+\.\d+$', text):
                opening_odd = text
                print(f"✓ Găsit opening odd: {opening_odd}")
                break
        
        # Închide popup
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        return opening_odd
        
    except Exception as e:
        print(f"Eroare get_opening_odds: {e}")
        return 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_exact_betano(ou_link, ah_link)
