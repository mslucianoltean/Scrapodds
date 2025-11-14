def scrape_any_bookmaker(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu orice bookmaker'}
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
        # OVER/UNDER - ORICE BOOKMAKER
        # ----------------------------------------------------
        print("=== OVER/UNDER - ORICE BOOKMAKER ===")
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
                
                # 3. GĂSEȘTE PRIMUL BOOKMAKER CU COTE VALIDE
                # Caută toate rândurile care conțin cote
                all_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row') or contains(@class, 'flex')]")
                print(f"Rânduri totale găsite: {len(all_rows)}")
                
                bookmaker_found = False
                for row in all_rows:
                    try:
                        row_text = row.text
                        if not row_text or len(row_text) > 200:
                            continue
                            
                        # Verifică dacă rândul conține cote
                        odds = re.findall(r'\d+\.\d+', row_text)
                        if len(odds) >= 2:
                            # Extrage numele bookmaker-ului (primul cuvânt)
                            bookmaker_name = "Unknown"
                            words = row_text.split()
                            if words:
                                bookmaker_name = words[0]
                            
                            # Găsește elementele pentru click
                            odds_elements = row.find_elements(By.XPATH, ".//*[contains(text(), '.') and string-length(text()) < 6]")
                            
                            if len(odds_elements) >= 2:
                                over_close = odds_elements[0].text
                                under_close = odds_elements[1].text
                                
                                # Extrage opening odds
                                over_open = get_opening_odds_simple(driver, odds_elements[0])
                                under_open = get_opening_odds_simple(driver, odds_elements[1])
                                
                                ou_lines.append({
                                    'Line': line_value,
                                    'Over_Close': over_close,
                                    'Over_Open': over_open,
                                    'Under_Close': under_close,
                                    'Under_Open': under_open,
                                    'Bookmaker': bookmaker_name
                                })
                                
                                print(f"✓ Găsit bookmaker: {bookmaker_name} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                                bookmaker_found = True
                                break
                                
                    except Exception as e:
                        continue
                
                if bookmaker_found:
                    break  # Am găsit un bookmaker, ieșim
                    
                # Click back
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"Eroare la linia OU {i+1}: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ORICE BOOKMAKER
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP - ORICE BOOKMAKER ===")
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
                
                # 3. GĂSEȘTE PRIMUL BOOKMAKER
                all_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row') or contains(@class, 'flex')]")
                print(f"Rânduri AH totale găsite: {len(all_rows)}")
                
                bookmaker_found = False
                for row in all_rows:
                    try:
                        row_text = row.text
                        if not row_text or len(row_text) > 200:
                            continue
                            
                        odds = re.findall(r'\d+\.\d+', row_text)
                        if len(odds) >= 2:
                            bookmaker_name = "Unknown"
                            words = row_text.split()
                            if words:
                                bookmaker_name = words[0]
                            
                            odds_elements = row.find_elements(By.XPATH, ".//*[contains(text(), '.') and string-length(text()) < 6]")
                            
                            if len(odds_elements) >= 2:
                                home_close = odds_elements[0].text
                                away_close = odds_elements[1].text
                                
                                home_open = get_opening_odds_simple(driver, odds_elements[0])
                                away_open = get_opening_odds_simple(driver, odds_elements[1])
                                
                                ah_lines.append({
                                    'Line': line_value,
                                    'Home_Close': home_close,
                                    'Home_Open': home_open,
                                    'Away_Close': away_close,
                                    'Away_Open': away_open,
                                    'Bookmaker': bookmaker_name
                                })
                                
                                print(f"✓ Găsit bookmaker AH: {bookmaker_name} | Home: {home_close}/{home_open} | Away: {away_close}/{away_open}")
                                bookmaker_found = True
                                break
                                
                    except Exception as e:
                        continue
                
                if bookmaker_found:
                    break
                    
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
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

def get_opening_odds_simple(driver, odds_element):
    """Extrage opening odds simplu"""
    try:
        original_odd = odds_element.text
        print(f"Click pentru opening odd: {original_odd}")
        
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(2)
        
        opening_odd = 'N/A'
        
        # Caută orice număr cu . care nu e cel original
        all_texts = driver.find_elements(By.XPATH, "//*")
        for elem in all_texts:
            text = elem.text.strip()
            if text and text != original_odd and re.match(r'^\d+\.\d+$', text):
                opening_odd = text
                print(f"✓ Opening odd găsit: {opening_odd}")
                break
        
        # Închide
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        return opening_odd
        
    except:
        return 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_any_bookmaker(ou_link, ah_link)
