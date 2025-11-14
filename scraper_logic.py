def scrape_with_exact_xpath(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu XPATH exact'}
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
        # OVER/UNDER - CU XPATH EXACT
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", ou_tab)
        print("✓ Click pe tab Over/Under")
        time.sleep(3)
        
        # 2. GĂSEȘTE TOATE LINIILE CU STRUCTURA SIMILARĂ
        ou_lines = []
        
        # XPATH-ul de bază (fără indexul final)
        base_xpath = "/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]"
        
        # Testează mai multe indexuri (de la 1 la 20)
        for i in range(1, 21):
            try:
                line_xpath = f"{base_xpath}/div[{i}]/div/div[1]/div"
                line_element = driver.find_element(By.XPATH, line_xpath)
                line_text = line_element.text
                
                if "Over/Under" in line_text:
                    print(f"✓ Linie {i} găsită: {line_text}")
                    
                    # CLICK PE LINIE
                    driver.execute_script("arguments[0].click();", line_element)
                    print("✓ Click pe linie")
                    time.sleep(3)
                    
                    # VERIFICĂ DACĂ S-AU DESCHIS BOOKMAKERII
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
                            
                            # Extrage linia exactă
                            line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                            line_value = line_match.group(1) if line_match else line_text
                            
                            # Extrage opening odds
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
                            break
                        
                    except Exception as e:
                        print(f"✗ Betano nu găsit pentru linia {i}: {e}")
                    
                    # ÎNCHIDE LINIA
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                    
            except Exception as e:
                # Linia nu există sau nu e clickable
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
        
        # Testează pentru Asian Handicap
        for i in range(1, 21):
            try:
                line_xpath = f"{base_xpath}/div[{i}]/div/div[1]/div"
                line_element = driver.find_element(By.XPATH, line_xpath)
                line_text = line_element.text
                
                if "Asian Handicap" in line_text:
                    print(f"✓ Linie AH {i} găsită: {line_text}")
                    
                    driver.execute_script("arguments[0].click();", line_element)
                    print("✓ Click pe linie AH")
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
                            
                            line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                            line_value = line_match.group(1) if line_match else line_text
                            
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
                            break
                        
                    except Exception as e:
                        print(f"✗ Betano nu găsit pentru AH linia {i}: {e}")
                    
                    driver.execute_script("arguments[0].click();", line_element)
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
    return scrape_with_exact_xpath(ou_link, ah_link)
