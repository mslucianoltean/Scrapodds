def scrape_debug_final(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Debug': 'Analiză finală'}
    driver = None
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("=== DEBUG COMPLET ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # 1. CLICK PE TAB OVER/UNDER
        ou_tab = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", ou_tab)
        print("✓ Click pe tab Over/Under")
        time.sleep(3)
        
        # 2. GĂSEȘTE LINIILE
        line_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under +') or contains(text(), 'Over/Under -')]")
        print(f"Linii găsite: {len(line_elements)}")
        
        if not line_elements:
            results['Error'] = "Nici o linie găsită"
            return results
        
        # 3. TESTEAZĂ PRIMA LINIE
        first_line = line_elements[0]
        print(f"Linia 1: {first_line.text}")
        
        # CLICK PE LINIE
        driver.execute_script("arguments[0].click();", first_line)
        time.sleep(3)
        
        # 4. CE VEDE DUPĂ CLICK?
        
        # A. Toate link-urile cu "betano"
        all_betano_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
        print(f"Link-uri Betano găsite: {len(all_betano_links)}")
        
        for i, link in enumerate(all_betano_links):
            href = link.get_attribute('href')
            text = link.text
            print(f"Betano {i}: href='{href}' | text='{text}'")
        
        # B. Toate elementele care arată a bookmakeri
        all_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row') or contains(@class, 'flex')]")
        print(f"Rânduri totale: {len(all_rows)}")
        
        bookmaker_rows = []
        for i, row in enumerate(all_rows[:10]):
            row_text = row.text.strip()
            if row_text and len(row_text) < 200:
                print(f"Rând {i}: {row_text[:100]}...")
                if any(word in row_text.lower() for word in ['betano', '1xbet', 'unibet', 'bet', 'odds']):
                    bookmaker_rows.append(row)
        
        print(f"Rânduri bookmaker: {len(bookmaker_rows)}")
        
        # C. Toate elementele cu cote
        all_odds = driver.find_elements(By.XPATH, "//*[contains(text(), '.')]")
        odds_found = []
        for elem in all_odds:
            text = elem.text.strip()
            if re.match(r'^\d+\.\d+$', text):
                odds_found.append(text)
        
        print(f"Cote găsite: {odds_found[:10]}")
        
        results['Betano_Links'] = len(all_betano_links)
        results['Bookmaker_Rows'] = len(bookmaker_rows)
        results['Odds_Found'] = len(odds_found)
        
        if all_betano_links:
            results['Betano_Example'] = {
                'href': all_betano_links[0].get_attribute('href'),
                'text': all_betano_links[0].text
            }
        
    except Exception as e:
        results['Error'] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return results

# FOLOSEȘTE DOAR ASTA!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_debug_final(ou_link, ah_link)
