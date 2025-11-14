def scrape_with_exact_selectors(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu selectori exacti'}
    driver = None
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # ----------------------------------------------------
        # OVER/UNDER - CU SELECTORI EXACTI
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", ou_tab)
        print("✓ Click pe tab Over/Under")
        time.sleep(3)
        
        # 2. SELECTORI EXACTI PENTRU LINII
        ou_lines = []
        
        # Selector pentru containerul liniei (div:nth-child(9))
        line_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'min-md:px-[10px]')]/div")
        print(f"Găsite {len(line_containers)} containere linii")
        
        for i, line_container in enumerate(line_containers[:15]):  # Primele 15 linii
            try:
                # Verifică dacă este linie Over/Under
                line_text_element = line_container.find_element(By.XPATH, ".//div[contains(@class, 'font-bold text-[#2F2F2F]')]")
                line_text = line_text_element.text
                
                if "Over/Under" in line_text:
                    print(f"✓ Linie OU {i+1}: {line_text}")
                    
                    # Extrage valoarea liniei
                    line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                    if not line_match:
                        continue
                    
                    line_value = line_match.group(1)
                    
                    # 3. CLICK PE SĂGEATĂ (selector exact)
                    arrow_container = line_container.find_element(By.XPATH, ".//div[contains(@class, 'min-w-[32px] max-w-[32px]')]")
                    arrow_element = arrow_container.find_element(By.XPATH, ".//div[contains(@class, 'bg-provider-arrow')]")
                    
                    print("✓ Găsită săgeată - click...")
                    driver.execute_script("arguments[0].click();", arrow_element)
                    time.sleep(3)
                    
                    # 4. VERIFICĂ DACA S-A DESCHIS
                    try:
                        betano_element = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//p[text()='Betano.ro']"))
                        )
                        print("✅ BETANO GĂSIT!")
                        
                        # EXTRAge DATELE
                        betano_row = betano_element.find_element(By.XPATH, "./ancestor::div[1]")
                        odds_elements = betano_row.find_elements(By.XPATH, ".//p[@class='odds-text']")
                        
                        if len(odds_elements) >= 2:
                            over_close = odds_elements[0].text
                            under_close = odds_elements[1].text
                            
                            # EXTRAge OPENING ODDS
                            odds_containers = betano_row.find_elements(By.XPATH, ".//div[@data-testid='odd-container']")
                            over_open = get_opening_odds(driver, odds_containers[0]) if odds_containers else 'N/A'
                            under_open = get_opening_odds(driver, odds_containers[1]) if len(odds_containers) > 1 else 'N/A'
                            
                            ou_lines.append({
                                'Line': line_value,
                                'Over_Close': over_close,
                                'Over_Open': over_open,
                                'Under_Close': under_close,
                                'Under_Open': under_open,
                                'Bookmaker': 'Betano.ro'
                            })
                            
                            print(f"🎉 LINIE COMPLETĂ: {line_value} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                            
                            # ÎNCHIDE LINIA
                            driver.execute_script("arguments[0].click();", arrow_element)
                            time.sleep(1)
                            break
                        else:
                            print("✗ Nu s-au găsit suficiente cote")
                            
                    except Exception as e:
                        print(f"✗ Betano nu găsit: {e}")
                    
                    # ÎNCHIDE LINIA
                    driver.execute_script("arguments[0].click();", arrow_element)
                    time.sleep(1)
                    
            except Exception as e:
                # Nu e linie Over/Under sau eroare
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEAȘI LOGICĂ
        # ----------------------------------------------------
        print("=== START ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(5)
        
        ah_tab = driver.find_element(By.XPATH, "//div[text()='Asian Handicap']")
        driver.execute_script("arguments[0].click();", ah_tab)
        print("✓ Click pe tab Asian Handicap")
        time.sleep(3)
        
        ah_lines = []
        
        # GĂSEȘTE LINIILE ASIAN HANDICAP
        ah_line_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'min-md:px-[10px]')]/div")
        print(f"Găsite {len(ah_line_containers)} containere AH")
        
        for i, line_container in enumerate(ah_line_containers[:15]):
            try:
                line_text_element = line_container.find_element(By.XPATH, ".//div[contains(@class, 'font-bold text-[#2F2F2F]')]")
                line_text = line_text_element.text
                
                if "Asian Handicap" in line_text:
                    print(f"✓ Linie AH {i+1}: {line_text}")
                    
                    line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                    if not line_match:
                        continue
                    
                    line_value = line_match.group(1)
                    
                    # CLICK PE SĂGEATĂ
                    arrow_container = line_container.find_element(By.XPATH, ".//div[contains(@class, 'min-w-[32px] max-w-[32px]')]")
                    arrow_element = arrow_container.find_element(By.XPATH, ".//div[contains(@class, 'bg-provider-arrow')]")
                    
                    print("✓ Click pe săgeată AH...")
                    driver.execute_script("arguments[0].click();", arrow_element)
                    time.sleep(3)
                    
                    try:
                        betano_element = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//p[text()='Betano.ro']"))
                        )
                        print("✅ BETANO GĂSIT PENTRU AH!")
                        
                        betano_row = betano_element.find_element(By.XPATH, "./ancestor::div[1]")
                        odds_elements = betano_row.find_elements(By.XPATH, ".//p[@class='odds-text']")
                        
                        if len(odds_elements) >= 2:
                            home_close = odds_elements[0].text
                            away_close = odds_elements[1].text
                            
                            odds_containers = betano_row.find_elements(By.XPATH, ".//div[@data-testid='odd-container']")
                            home_open = get_opening_odds(driver, odds_containers[0]) if odds_containers else 'N/A'
                            away_open = get_opening_odds(driver, odds_containers[1]) if len(odds_containers) > 1 else 'N/A'
                            
                            ah_lines.append({
                                'Line': line_value,
                                'Home_Close': home_close,
                                'Home_Open': home_open,
                                'Away_Close': away_close,
                                'Away_Open': away_open,
                                'Bookmaker': 'Betano.ro'
                            })
                            
                            print(f"🎉 LINIE AH COMPLETĂ: {line_value} | Home: {home_close}/{home_open} | Away: {away_close}/{away_open}")
                            
                            driver.execute_script("arguments[0].click();", arrow_element)
                            time.sleep(1)
                            break
                            
                    except Exception as e:
                        print(f"✗ Betano nu găsit pentru AH: {e}")
                    
                    driver.execute_script("arguments[0].click();", arrow_element)
                    time.sleep(1)
                    
            except Exception as e:
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds(driver, odds_container):
    try:
        current_odd_element = odds_container.find_element(By.XPATH, ".//p[@class='odds-text']")
        current_odd = current_odd_element.text
        print(f"Click pentru opening odd: {current_odd}")
        
        driver.execute_script("arguments[0].click();", odds_container)
        time.sleep(2)
        
        opening_odd = 'N/A'
        all_elements = driver.find_elements(By.XPATH, "//*")
        
        for elem in all_elements:
            text = elem.text.strip()
            if text and text != current_odd and re.match(r'^\d+\.\d+$', text):
                opening_odd = text
                break
        
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        return opening_odd
        
    except:
        return 'N/A'

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_with_exact_selectors(ou_link, ah_link)
