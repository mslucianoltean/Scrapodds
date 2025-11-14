def scrape_with_any_bookmaker(ou_link, ah_link):
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
        # OVER/UNDER - CU ORICE BOOKMAKER
        # ----------------------------------------------------
        print("=== OVER/UNDER CU ORICE BOOKMAKER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. GĂSEȘTE ȘI CLICK PE TAB OVER/UNDER
        ou_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        for tab in ou_tabs:
            if tab.text == "Over/Under":
                driver.execute_script("arguments[0].click();", tab)
                print("✓ Click pe tab Over/Under")
                time.sleep(3)
                break
        
        # 2. GĂSEȘTE LINIILE CU "Over/Under +222.5"
        ou_lines = []
        line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under +')]")
        print(f"Găsite {len(line_elements)} linii OU")
        
        for line_element in line_elements[:2]:  # Primele 2 linii
            try:
                line_text = line_element.text
                print(f"Procesez linia: {line_text}")
                
                # Extrage valoarea liniei
                line_match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                # CLICK PE LINIE
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # 3. GĂSEȘTE PRIMUL BOOKMAKER DISPONIBIL (orice bookmaker)
                bookmaker_selectors = [
                    "//div[contains(@class, 'row')]//div[contains(@class, 'odds')]",
                    "//*[contains(text(), '.') and string-length(text()) < 6]/ancestor::div[contains(@class, 'row')][1]",
                    "//div[contains(@class, 'flex')]//div[contains(text(), '.')]"
                ]
                
                bookmaker_found = False
                for selector in bookmaker_selectors:
                    try:
                        bookmaker_rows = driver.find_elements(By.XPATH, selector)
                        for row in bookmaker_rows[:5]:  # Primele 5 rânduri
                            try:
                                row_text = row.text
                                # Verifică dacă are formă de cote (numere cu .)
                                odds = re.findall(r'\d+\.\d+', row_text)
                                if len(odds) >= 2:
                                    # Găsește numele bookmaker-ului (primul cuvânt din text)
                                    bookmaker_name = row_text.split()[0] if row_text.split() else 'Unknown'
                                    
                                    ou_lines.append({
                                        'Line': line_value,
                                        'Home_Over_Close': odds[0],
                                        'Home_Over_Open': 'N/A',
                                        'Away_Under_Close': odds[1],
                                        'Away_Under_Open': 'N/A', 
                                        'Bookmaker': bookmaker_name,
                                        'Debug_Raw': row_text[:100]
                                    })
                                    
                                    print(f"✓ Găsit bookmaker: {bookmaker_name} - {odds[0]}/{odds[1]}")
                                    bookmaker_found = True
                                    break
                            except:
                                continue
                        if bookmaker_found:
                            break
                    except:
                        continue
                
                if bookmaker_found:
                    break  # Am găsit o linie cu bookmaker
                    
            except Exception as e:
                print(f"Eroare la linia: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEEAȘI LOGICĂ
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP CU ORICE BOOKMAKER ===")
        driver.get(ah_link)
        time.sleep(5)
        
        # Găsește tab Asian Handicap
        ah_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        for tab in ah_tabs:
            if "Asian Handicap" in tab.text:
                driver.execute_script("arguments[0].click();", tab)
                print("✓ Click pe tab Asian Handicap")
                time.sleep(3)
                break
        
        # Găsește linii Asian Handicap
        ah_lines = []
        ah_line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
        print(f"Găsite {len(ah_line_elements)} linii AH")
        
        for line_element in ah_line_elements[:2]:
            try:
                line_text = line_element.text
                print(f"Procesez linia AH: {line_text}")
                
                line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                if not line_match:
                    continue
                    
                line_value = line_match.group(1)
                
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # Caută bookmaker pentru AH
                bookmaker_found = False
                for selector in bookmaker_selectors:
                    try:
                        bookmaker_rows = driver.find_elements(By.XPATH, selector)
                        for row in bookmaker_rows[:5]:
                            try:
                                row_text = row.text
                                odds = re.findall(r'\d+\.\d+', row_text)
                                if len(odds) >= 2:
                                    bookmaker_name = row_text.split()[0] if row_text.split() else 'Unknown'
                                    
                                    ah_lines.append({
                                        'Line': line_value,
                                        'Home_Over_Close': odds[0],
                                        'Home_Over_Open': 'N/A',
                                        'Away_Under_Close': odds[1],
                                        'Away_Under_Open': 'N/A',
                                        'Bookmaker': bookmaker_name,
                                        'Debug_Raw': row_text[:100]
                                    })
                                    
                                    print(f"✓ Găsit bookmaker AH: {bookmaker_name} - {odds[0]}/{odds[1]}")
                                    bookmaker_found = True
                                    break
                            except:
                                continue
                        if bookmaker_found:
                            break
                    except:
                        continue
                
                if bookmaker_found:
                    break
                    
            except Exception as e:
                print(f"Eroare la linia AH: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_with_any_bookmaker(ou_link, ah_link)
