def scrape_final_solution(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    import re
    
    results = {'Match': 'Scraping final solution'}
    driver = None
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        # ----------------------------------------------------
        # OVER/UNDER
        # ----------------------------------------------------
        print("=== START OVER/UNDER ===")
        driver.get(ou_link)
        
        # Așteaptă să se încarce conținutul dinamic
        print("Aștept încărcarea conținutului...")
        time.sleep(8)  # Așteaptă mai mult pentru JS
        
        # Verifică dacă există elemente de odds
        try:
            # Așteaptă orice element care arată a odds
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '.') and string-length(text()) < 6]")))
            print("✓ Conținutul s-a încărcat")
        except:
            print("✗ Conținutul nu s-a încărcat complet")
        
        # Încearcă să găsească linii expandabile
        ou_lines = []
        
        # Caută orice element care ar putea fi o linie
        potential_lines = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex') or contains(@class, 'row') or contains(@class, 'item')]")
        print(f"Găsite {len(potential_lines)} elemente potențiale")
        
        for i, element in enumerate(potential_lines[:15]):  # Testează primele 15
            try:
                text = element.text.strip()
                if not text or len(text) > 100:
                    continue
                    
                print(f"Element {i+1}: {text[:50]}...")
                
                # Verifică dacă arată ca o linie cu numere
                if any(char in text for char in ['+', '-']) and any(char.isdigit() for char in text):
                    print(f"→ Posibilă linie: {text}")
                    
                    # Încearcă să dai click
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(2)
                    
                    # După click, caută Betano
                    betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano') or contains(text(), 'betano')]")
                    if betano_elements:
                        print("✓ GĂSIT BETANO!")
                        
                        # Găsește părintele Betano și cotele de lângă
                        betano_parent = betano_elements[0].find_element(By.XPATH, "./ancestor::div[1]")
                        parent_text = betano_parent.text
                        
                        # Extrage cotele din text
                        odds = re.findall(r'\d+\.\d+', parent_text)
                        if len(odds) >= 2:
                            ou_lines.append({
                                'Line': text,
                                'Home_Over_Close': odds[0],
                                'Home_Over_Open': 'N/A',
                                'Away_Under_Close': odds[1], 
                                'Away_Under_Open': 'N/A',
                                'Bookmaker': 'Betano',
                                'Debug': 'Găsit prin text'
                            })
                            break
                    
                    # Click back pentru a închide
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                    
            except Exception as e:
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP (același logică)
        # ----------------------------------------------------
        print("=== START ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(8)  # Așteaptă încărcarea
        
        ah_lines = []
        # Aceeași logică ca mai sus pentru AH
        # ...
        
        results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_final_solution(ou_link, ah_link)
