def scrape_with_js_wait(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os
    import time
    import re
    
    results = {'Match': 'Scraping cu așteptare JS'}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)
        
        print("=== SCRAPING CU AȘTEPTARE JS ===")
        
        # ----------------------------------------------------
        # OVER/UNDER
        # ----------------------------------------------------
        print("=== OVER/UNDER ===")
        driver.get(ou_link)
        
        # Așteaptă ca elementele specifice să se încarce
        print("Aștept încărcare JavaScript...")
        
        # Așteaptă tab-ul Over/Under să fie prezent
        try:
            ou_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//div[text()='Over/Under']")))
            print("✓ Tab Over/Under încărcat")
        except:
            print("✗ Tab Over/Under nu s-a încărcat")
        
        # Așteaptă ca liniile să se încarce
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Over/Under +')]")))
            print("✓ Linii Over/Under încărcate")
        except:
            print("✗ Linii nu s-au încărcat")
        
        # Așteaptă încă 5 secunde pentru datele dinamice
        print("Aștept date dinamice...")
        time.sleep(5)
        
        # Verifică dacă Betano s-a încărcat
        betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano')]")
        print(f"Elemente Betano găsite: {len(betano_elements)}")
        
        # Salvează page_source după așteptare
        ou_html = driver.page_source
        print(f"Lungime HTML OU după așteptare: {len(ou_html)}")
        
        # Extrage datele
        ou_lines = []
        if betano_elements:
            print("✓ Betano este în pagină - încerc extragere...")
            ou_lines = extract_data_with_selenium(driver, "Over/Under")
        else:
            print("✗ Betano NU este în pagină chiar și după așteptare")
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP ===")
        driver.get(ah_link)
        
        print("Aștept încărcare JavaScript AH...")
        
        # Așteaptă tab-ul Asian Handicap
        try:
            ah_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//div[text()='Asian Handicap']")))
            print("✓ Tab Asian Handicap încărcat")
        except:
            print("✗ Tab Asian Handicap nu s-a încărcat")
        
        # Așteaptă liniile AH
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Asian Handicap')]")))
            print("✓ Linii Asian Handicap încărcate")
        except:
            print("✗ Linii AH nu s-au încărcat")
        
        print("Aștept date dinamice AH...")
        time.sleep(5)
        
        # Verifică Betano pentru AH
        ah_betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano')]")
        print(f"Elemente Betano AH găsite: {len(ah_betano_elements)}")
        
        ah_lines = []
        if ah_betano_elements:
            print("✓ Betano este în pagină AH - încerc extragere...")
            ah_lines = extract_data_with_selenium(driver, "Asian Handicap")
        
        results['Handicap_Lines'] = ah_lines
        
        # DEBUG INFO
        results['Debug'] = {
            'ou_betano_elements': len(betano_elements),
            'ah_betano_elements': len(ah_betano_elements),
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines)
        }
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def extract_data_with_selenium(driver, market_type):
    """Extrage datele folosind Selenium după ce JS s-a încărcat"""
    lines = []
    
    print(f"Extragere {market_type} cu Selenium...")
    
    # Găsește toate containerele de linii
    line_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'min-md:px-[10px]')]/div")
    print(f"Containere linii găsite: {len(line_containers)}")
    
    for i, container in enumerate(line_containers[:10]):
        try:
            # Verifică dacă este linie corectă
            text_elements = container.find_elements(By.XPATH, ".//div[contains(@class, 'font-bold text-[#2F2F2F]')]")
            if not text_elements:
                continue
                
            line_text = text_elements[0].text
            if market_type in line_text:
                print(f"✓ {market_type} linie {i+1}: {line_text}")
                
                # Extrage valoarea liniei
                line_match = re.search(rf'{market_type}\s*([+-]?\d+\.?\d*)', line_text)
                line_value = line_match.group(1) if line_match else 'N/A'
                
                # Încearcă să găsești Betano în acest container
                betano_in_container = container.find_elements(By.XPATH, ".//*[contains(text(), 'Betano')]")
                if betano_in_container:
                    print(f"  ✅ Betano găsit în linia {i+1}")
                    
                    # Extrage cotele din container
                    odds_elements = container.find_elements(By.XPATH, ".//p[@class='odds-text']")
                    if len(odds_elements) >= 2:
                        odds = [elem.text for elem in odds_elements[:2]]
                        
                        line_data = {
                            'Line': line_value,
                            f'{"Over" if market_type == "Over/Under" else "Home"}_Close': odds[0],
                            f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                            f'{"Under" if market_type == "Over/Under" else "Away"}_Close': odds[1],
                            f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                            'Bookmaker': 'Betano.ro'
                        }
                        
                        lines.append(line_data)
                        print(f"  ✅ Date extrase: {line_value} | {odds[0]}/{odds[1]}")
                        
        except Exception as e:
            continue
    
    return lines

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_with_js_wait(ou_link, ah_link)
