def scrape_fix_click_issue(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu fix click'}
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
        # OVER/UNDER - CU CLICK CORECT
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", ou_tab)
        print("✓ Click pe tab Over/Under")
        time.sleep(3)
        
        # 2. GĂSEȘTE LINIILE - SELECTOR CORECT PENTRU CLICK
        ou_lines = []
        
        # Selectori diferiți pentru liniile clickable
        line_selectors = [
            "//div[contains(text(), 'Over/Under +') or contains(text(), 'Over/Under -')]",
            "//*[contains(@class, 'table-main') and contains(text(), 'Over/Under')]",
            "//div[contains(@class, 'row') and contains(text(), 'Over/Under')]"
        ]
        
        line_elements = []
        for selector in line_selectors:
            try:
                line_elements = driver.find_elements(By.XPATH, selector)
                if line_elements:
                    print(f"Găsite {len(line_elements)} linii OU cu selector: {selector}")
                    break
            except:
                continue
        
        if not line_elements:
            print("✗ Nicio linie găsită cu niciun selector")
            results['Error'] = "Nicio linie găsită"
            return results
        
        for i, line_element in enumerate(line_elements[:5]):
            try:
                line_text = line_element.text
                print(f"Procesez linia OU {i+1}: {line_text}")
                
                line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                # 3. CLICK CORECT PE LINIE - cu mai multe încercări
                print("Încerc click pe linie...")
                
                # Încearcă click direct
                try:
                    driver.execute_script("arguments[0].click();", line_element)
                    print("✓ Click cu JavaScript")
                except:
                    # Încearcă click normal
                    try:
                        line_element.click()
                        print("✓ Click normal")
                    except:
                        print("✗ Click eșuat")
                        continue
                
                # 4. AȘTEPTĂ SĂ SE DESCHIDĂ BOOKMAKERII
                print("Aștept deschidere bookmakeri...")
                time.sleep(3)
                
                # Verifică dacă s-au deschis bookmakerii
                # Caută orice element care arată a bookmaker
                bookmaker_indicators = [
                    "//p[text()='Betano.ro']",
                    "//div[contains(@class, 'bookmaker')]",
                    "//div[@data-testid='over-under-expanded-row']",
                    "//*[contains(text(), '1xbet') or contains(text(), 'unibet') or contains(text(), 'bet365')]"
                ]
                
                bookmakers_found = False
                for indicator in bookmaker_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator)
                        if elements:
                            print(f"✓ Bookmakeri găsiți cu: {indicator}")
                            bookmakers_found = True
                            break
                    except:
                        continue
                
                if not bookmakers_found:
                    print("✗ Bookmakerii NU s-au deschis după click")
                    # Încearcă alt click sau continuă
                    continue
                
                # 5. ACUM CAUTĂ BETANO
                try:
                    betano_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, "//p[text()='Betano.ro']"))
                    )
                    print("✅ BETANO GĂSIT!")
                    
                    # Restul codului pentru extragere cote...
                    betano_row = betano_element.find_element(By.XPATH, "./ancestor::div[1]")
                    odds_elements = betano_row.find_elements(By.XPATH, ".//p[@class='odds-text']")
                    
                    if len(odds_elements) >= 2:
                        over_close = odds_elements[0].text
                        under_close = odds_elements[1].text
                        
                        print(f"✓ Cote găsite: Over={over_close}, Under={under_close}")
                        
                        # Extrage opening odds...
                        odds_containers = betano_row.find_elements(By.XPATH, ".//div[@data-testid='odd-container']")
                        
                        over_open = get_opening_odds_simple(driver, odds_containers[0]) if odds_containers else 'N/A'
                        under_open = get_opening_odds_simple(driver, odds_containers[1]) if len(odds_containers) > 1 else 'N/A'
                        
                        ou_lines.append({
                            'Line': line_value,
                            'Over_Close': over_close,
                            'Over_Open': over_open,
                            'Under_Close': under_close,
                            'Under_Open': under_open,
                            'Bookmaker': 'Betano.ro'
                        })
                        
                        print(f"🎉 LINIE OU COMPLETĂ: {line_value} | Over: {over_close}/{over_open} | Under: {under_close}/{under_open}")
                        break
                    
                except Exception as e:
                    print(f"✗ Betano nu găsit după deschidere: {e}")
                
                # Închide linia pentru următoarea
                try:
                    driver.execute_script("arguments[0].click();", line_element)
                    time.sleep(1)
                except:
                    pass
                    
            except Exception as e:
                print(f"✗ Eroare linia OU {i+1}: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ASIAN HANDICAP - aceeași logică...
        results['Handicap_Lines'] = []
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def get_opening_odds_simple(driver, odds_container):
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
    return scrape_fix_click_issue(ou_link, ah_link)
