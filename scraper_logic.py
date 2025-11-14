def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping final cu selectorii exacti'}
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
        # OVER/UNDER - CU SELECTORI EXACȚI
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        try:
            ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
            driver.execute_script("arguments[0].click();", ou_tab)
            print("✓ Click pe tab Over/Under")
            time.sleep(3)
        except Exception as e:
            print(f"✗ Eroare tab OU: {e}")
        
        # 2. GĂSEȘTE LINIILE OVER/UNDER
        ou_lines = []
        try:
            line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under +') or contains(text(), 'Over/Under -')]")
            print(f"Găsite {len(line_elements)} linii OU")
        except:
            line_elements = []
            print("✗ Nu s-au găsit linii OU")
        
        for i, line_element in enumerate(line_elements[:3]):  # Testează doar primele 3
            try:
                line_text = line_element.text
                print(f"Procesez linia OU {i+1}: {line_text}")
                
                # Extrage valoarea liniei
                line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    print("✗ Nu s-a putut extrage valoarea liniei")
                    continue
                    
                line_value = line_match.group(1)
                print(f"✓ Valoare linie: {line_value}")
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # 3. GĂSEȘTE BETANO (selector exact din console)
                try:
                    betano_link = driver.find_element(By.XPATH, "//a[text()='Betano.ro']")
                    print("✓ Găsit Betano.ro")
                except:
                    print("✗ Betano.ro nu găsit")
                    # Încearcă click back și continuă
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                    continue
                
                # 4. GĂSEȘTE RÂNDUL BETANO
                try:
                    betano_row = betano_link.find_element(By.XPATH, "./ancestor::div[1]")
                except:
                    betano_row = betano_link
                
                # 5. EXTRAge COTELE CLOSE
                try:
                    # Încearcă mai mulți selectori pentru cote
                    odds_selectors = [
                        ".//p[contains(@class, 'height-content')]",
                        ".//div[contains(@class, 'odds-cell')]//div[contains(text(), '.')]",
                        ".//*[contains(text(), '.') and string-length(text()) < 6]"
                    ]
                    
                    odds_elements = []
                    for selector in odds_selectors:
                        try:
                            elements = betano_row.find_elements(By.XPATH, selector)
                            if len(elements) >= 2:
                                odds_elements = elements
                                break
                        except:
                            continue
                    
                    if len(odds_elements) >= 2:
                        over_close = odds_elements[0].text
                        under_close = odds_elements[1].text
                        
                        print(f"✓ Cote găsite: Over={over_close}, Under={under_close}")
                        
                        # 6. EXTRAge OPENING ODDS
                        over_open = get_opening_odds_simple(driver, odds_elements[0])
                        under_open = get_opening_odds_simple(driver, odds_elements[1])
                        
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
                    else:
                        print("✗ Nu s-au găsit suficiente cote")
                        
                except Exception as e:
                    print(f"✗ Eroare la extragerea cotelor: {e}")
                
                # Click back
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"✗ Eroare la linia OU {i+1}: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEAȘI LOGICĂ
        # ----------------------------------------------------
        print("=== START ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB ASIAN HANDICAP
        try:
            ah_tab = driver.find_element(By.XPATH, "//div[text()='Asian Handicap']")
            driver.execute_script("arguments[0].click();", ah_tab)
            print("✓ Click pe tab Asian Handicap")
            time.sleep(3)
        except Exception as e:
            print(f"✗ Eroare tab AH: {e}")
        
        # 2. GĂSEȘTE LINIILE ASIAN HANDICAP
        ah_lines = []
        try:
            ah_line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap +') or contains(text(), 'Asian Handicap -')]")
            print(f"Găsite {len(ah_line_elements)} linii AH")
        except:
            ah_line_elements = []
            print("✗ Nu s-au găsit linii AH")
        
        for i, line_element in enumerate(ah_line_elements[:3]):
            try:
                line_text = line_element.text
                print(f"Procesez linia AH {i+1}: {line_text}")
                
                line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    print("✗ Nu s-a putut extrage valoarea liniei AH")
                    continue
                    
                line_value = line_match.group(1)
                print(f"✓ Valoare linie AH: {line_value}")
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # 3. GĂSEȘTE BETANO
                try:
                    betano_link = driver.find_element(By.XPATH, "//a[text()='Betano.ro']")
                    print("✓ Găsit Betano.ro pentru AH")
                except:
                    print("✗ Betano.ro nu găsit pentru AH")
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                    continue
                
                # 4. GĂSEȘTE RÂNDUL BETANO
                try:
                    betano_row = betano_link.find_element(By.XPATH, "./ancestor::div[1]")
                except:
                    betano_row = betano_link
                
                # 5. EXTRAge COTELE CLOSE
                try:
                    odds_selectors = [
                        ".//p[contains(@class, 'height-content')]",
                        ".//div[contains(@class, 'odds-cell')]//div[contains(text(), '.')]",
                        ".//*[contains(text(), '.') and string-length(text()) < 6]"
                    ]
                    
                    odds_elements = []
                    for selector in odds_selectors:
                        try:
                            elements = betano_row.find_elements(By.XPATH, selector)
                            if len(elements) >= 2:
                                odds_elements = elements
                                break
                        except:
                            continue
                    
                    if len(odds_elements) >= 2:
                        home_close = odds_elements[0].text
                        away_close = odds_elements[1].text
                        
                        print(f"✓ Cote AH găsite: Home={home_close}, Away={away_close}")
                        
                        # 6. EXTRAge OPENING ODDS
                        home_open = get_opening_odds_simple(driver, odds_elements[0])
                        away_open = get_opening_odds_simple(driver, odds_elements[1])
                        
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
                    else:
                        print("✗ Nu s-au găsit suficiente cote AH")
                        
                except Exception as e:
                    print(f"✗ Eroare la extragerea cotelor AH: {e}")
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(1)
                    
            except Exception as e:
                print(f"✗ Eroare la linia AH {i+1}: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
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
        all_elements = driver.find_elements(By.XPATH, "//*")
        for elem in all_elements:
            text = elem.text.strip()
            if text and text != original_odd and re.match(r'^\d+\.\d+$', text):
                opening_odd = text
                print(f"✓ Opening odd găsit: {opening_odd}")
                break
        
        # Închide
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        return opening_odd
        
    except Exception as e:
        print(f"Eroare opening odds: {e}")
        return 'N/A'
