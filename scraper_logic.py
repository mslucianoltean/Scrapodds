def scrape_correct_logic(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu logica corectă'}
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
        # OVER/UNDER - LOGICA CORECTĂ
        # ----------------------------------------------------
        print("=== OVER/UNDER CORECT ===")
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
        
        # 2. GĂSEȘTE TOATE LINIILE OVER/UNDER
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
                
                # 3. GĂSEȘTE BETANO PRIN HREF
                betano_row = None
                try:
                    betano_row = driver.find_element(By.XPATH, "//a[contains(@href, 'betano.ro')]/ancestor::div[contains(@class, 'row') or contains(@class, 'flex')][1]")
                    print("✓ Găsit Betano")
                except:
                    print("✗ Betano nu găsit la această linie")
                    continue
                
                # 4. EXTRAge COTELE CLOSE (cele afișate)
                odds_elements = betano_row.find_elements(By.XPATH, ".//*[contains(text(), '.') and string-length(text()) < 6]")
                if len(odds_elements) >= 2:
                    over_close = odds_elements[0].text
                    under_close = odds_elements[1].text
                    
                    # 5. EXTRAge OVER OPEN (click pe over close)
                    over_open = get_opening_odds(driver, odds_elements[0])
                    
                    # 6. EXTRAge UNDER OPEN (click pe under close)  
                    under_open = get_opening_odds(driver, odds_elements[1])
                    
                    ou_lines.append({
                        'Line': line_value,
                        'Over_Close': over_close,
                        'Over_Open': over_open,
                        'Under_Close': under_close,
                        'Under_Open': under_open,
                        'Bookmaker': 'Betano'
                    })
                    
                    print(f"✓ Linie OU completă: {line_value} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                    break  # O linie cu Betano e suficientă
                    
            except Exception as e:
                print(f"Eroare la linia OU {i+1}: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - LOGICA CORECTĂ
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP CORECT ===")
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
                betano_row = None
                try:
                    betano_row = driver.find_element(By.XPATH, "//a[contains(@href, 'betano.ro')]/ancestor::div[contains(@class, 'row') or contains(@class, 'flex')][1]")
                    print("✓ Găsit Betano pentru AH")
                except:
                    print("✗ Betano nu găsit la această linie AH")
                    continue
                
                # 4. EXTRAge COTELE CLOSE
                odds_elements = betano_row.find_elements(By.XPATH, ".//*[contains(text(), '.') and string-length(text()) < 6]")
                if len(odds_elements) >= 2:
                    home_close = odds_elements[0].text
                    away_close = odds_elements[1].text
                    
                    # 5. EXTRAge HOME OPEN
                    home_open = get_opening_odds(driver, odds_elements[0])
                    
                    # 6. EXTRAge AWAY OPEN
                    away_open = get_opening_odds(driver, odds_elements[1])
                    
                    ah_lines.append({
                        'Line': line_value,
                        'Home_Close': home_close,
                        'Home_Open': home_open,
                        'Away_Close': away_close,
                        'Away_Open': away_open,
                        'Bookmaker': 'Betano'
                    })
                    
                    print(f"✓ Linie AH completă: {line_value} | Home: {home_close}/{home_open} | Away: {away_close}/{away_open}")
                    break
                    
            except Exception as e:
                print(f"Eroare la linia AH {i+1}: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds(driver, odds_element):
    """Extrage opening odds din popup după click pe o cotă"""
    try:
        # Salvează cota originală pentru comparație
        original_odd = odds_element.text
        
        # Click pe cota close
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(1.5)
        
        # Caută opening odds în popup
        opening_odd = 'N/A'
        
        # Încearcă mai mulți selectori pentru popup
        popup_selectors = [
            "//*[contains(@class, 'tooltip')]//*[contains(text(), '.')]",
            "//*[contains(@class, 'popup')]//*[contains(text(), '.')]",
            "//*[@id='tooltip_v']//*[contains(text(), '.')]",
            "//*[contains(text(), 'Opening odds')]//following-sibling::*[contains(text(), '.')]"
        ]
        
        for selector in popup_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and text != original_odd and re.match(r'^\d+\.\d+$', text):
                        opening_odd = text
                        print(f"✓ Găsit opening odd: {opening_odd}")
                        break
                if opening_odd != 'N/A':
                    break
            except:
                continue
        
        # Închide popup
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(0.5)
        
        return opening_odd
        
    except Exception as e:
        print(f"Eroare la get_opening_odds: {e}")
        return 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_correct_logic(ou_link, ah_link)
