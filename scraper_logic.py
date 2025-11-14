def scrape_final_exact(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu selector exact'}
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
        # OVER/UNDER - CU SELECTOR EXACT
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", ou_tab)
        print("✓ Click pe tab Over/Under")
        time.sleep(3)
        
        # 2. GĂSEȘTE LINIILE
        ou_lines = []
        line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under +') or contains(text(), 'Over/Under -')]")
        print(f"Găsite {len(line_elements)} linii OU")
        
        for i, line_element in enumerate(line_elements[:3]):
            try:
                line_text = line_element.text
                print(f"Procesez linia OU {i+1}: {line_text}")
                
                line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(3)
                
                # 3. SELECTOR EXACT PENTRU BETANO
                betano_element = driver.find_element(By.XPATH, "//p[@data-testid='outrights-expanded-bookmaker-name' and text()='Betano.ro']")
                print("✓ Găsit Betano.ro")
                
                # 4. GĂSEȘTE RÂNDUL BETANO (părintele)
                betano_row = betano_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or contains(@class, 'flex')][1]")
                
                # 5. EXTRAge COTELE
                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'height-content') and contains(text(), '.')]")
                
                if len(odds_elements) >= 2:
                    over_close = odds_elements[0].text
                    under_close = odds_elements[1].text
                    
                    print(f"✓ Cote găsite: Over={over_close}, Under={under_close}")
                    
                    # 6. EXTRAge OPENING ODDS
                    over_open = get_opening_odds(driver, odds_elements[0])
                    under_open = get_opening_odds(driver, odds_elements[1])
                    
                    ou_lines.append({
                        'Line': line_value,
                        'Over_Close': over_close,
                        'Over_Open': over_open,
                        'Under_Close': under_close,
                        'Under_Open': under_open,
                        'Bookmaker': 'Betano.ro'
                    })
                    
                    print(f"✅ LINIE OU COMPLETĂ: {line_value} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                    break
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"✗ Eroare linia OU {i+1}: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP
        # ----------------------------------------------------
        print("=== START ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(5)
        
        ah_tab = driver.find_element(By.XPATH, "//div[text()='Asian Handicap']")
        driver.execute_script("arguments[0].click();", ah_tab)
        print("✓ Click pe tab Asian Handicap")
        time.sleep(3)
        
        ah_lines = []
        ah_line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap +') or contains(text(), 'Asian Handicap -')]")
        print(f"Găsite {len(ah_line_elements)} linii AH")
        
        for i, line_element in enumerate(ah_line_elements[:3]):
            try:
                line_text = line_element.text
                print(f"Procesez linia AH {i+1}: {line_text}")
                
                line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(3)
                
                # GĂSEȘTE BETANO
                betano_element = driver.find_element(By.XPATH, "//p[@data-testid='outrights-expanded-bookmaker-name' and text()='Betano.ro']")
                print("✓ Găsit Betano.ro pentru AH")
                
                betano_row = betano_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or contains(@class, 'flex')][1]")
                odds_elements = betano_row.find_elements(By.XPATH, ".//p[contains(@class, 'height-content') and contains(text(), '.')]")
                
                if len(odds_elements) >= 2:
                    home_close = odds_elements[0].text
                    away_close = odds_elements[1].text
                    
                    print(f"✓ Cote AH găsite: Home={home_close}, Away={away_close}")
                    
                    home_open = get_opening_odds(driver, odds_elements[0])
                    away_open = get_opening_odds(driver, odds_elements[1])
                    
                    ah_lines.append({
                        'Line': line_value,
                        'Home_Close': home_close,
                        'Home_Open': home_open,
                        'Away_Close': away_close,
                        'Away_Open': away_open,
                        'Bookmaker': 'Betano.ro'
                    })
                    
                    print(f"✅ LINIE AH COMPLETĂ: {line_value} | Home: {home_close}/{home_open} | Away: {away_close}/{away_open}")
                    break
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"✗ Eroare linia AH {i+1}: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds(driver, odds_element):
    try:
        original_odd = odds_element.text
        print(f"Click pentru opening odd: {original_odd}")
        
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(2)
        
        opening_odd = 'N/A'
        
        # Caută opening odds în tooltip
        try:
            tooltip = driver.find_element(By.XPATH, "//div[contains(@class, 'tooltip') or contains(@class, 'popup')]")
            all_text = tooltip.text
            odds_in_tooltip = re.findall(r'\d+\.\d+', all_text)
            for odd in odds_in_tooltip:
                if odd != original_odd:
                    opening_odd = odd
                    break
        except:
            # Caută în tot documentul
            all_elements = driver.find_elements(By.XPATH, "//*")
            for elem in all_elements:
                text = elem.text.strip()
                if text and text != original_odd and re.match(r'^\d+\.\d+$', text):
                    opening_odd = text
                    break
        
        print(f"✓ Opening odd: {opening_odd}")
        
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        return opening_odd
        
    except:
        return 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_final_exact(ou_link, ah_link)
