def scrape_debug_complete(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    
    results = {'Debug': 'Analiză completă'}
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
        # DEBUG OVER/UNDER
        # ----------------------------------------------------
        print("=== DEBUG OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(8)  # Așteaptă mai mult
        
        # 1. Ce elemente cu text "Over/Under" există?
        ou_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over/Under')]")
        results['OU_Elements_Found'] = len(ou_elements)
        results['OU_Elements_Text'] = [elem.text for elem in ou_elements[:3]]
        
        # 2. Ce elemente cu clasa care conține "table" există?
        table_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'table')]")
        results['Table_Elements_Found'] = len(table_elements)
        results['Table_Classes'] = [elem.get_attribute('class') for elem in table_elements[:3]]
        
        # 3. Ce elemente cu clasa care conține "row" există?
        row_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'row')]")
        results['Row_Elements_Found'] = len(row_elements)
        
        # 4. Ce elemente cu clasa care conține "odds" există?
        odds_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'odds')]")
        results['Odds_Elements_Found'] = len(odds_elements)
        
        # 5. Există elemente cu "Betano"?
        betano_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano') or contains(text(), 'betano')]")
        results['Betano_Elements_Found'] = len(betano_elements)
        
        # 6. Ce butoane/div-uri clickable există?
        clickable_elements = driver.find_elements(By.XPATH, "//button | //div[@onclick] | //div[contains(@class, 'click')]")
        results['Clickable_Elements'] = len(clickable_elements)
        
        # 7. Salvează screenshot să vedem ce vede
        driver.save_screenshot('/tmp/debug_screenshot.png')
        results['Screenshot'] = 'Salvat'
        
        # 8. Extrage un sample din page source
        page_source = driver.page_source
        results['Page_Source_Length'] = len(page_source)
        
        # Caută pattern-uri specifice în page source
        if 'Over/Under' in page_source:
            results['OU_In_Source'] = 'DA'
        else:
            results['OU_In_Source'] = 'NU'
            
        if 'betano' in page_source.lower():
            results['Betano_In_Source'] = 'DA' 
        else:
            results['Betano_In_Source'] = 'NU'
        
        print("=== DEBUG COMPLET ===")
        
    except Exception as e:
        results['Error'] = str(e)
    finally:
        if driver:
            driver.quit()
    
    return results

# FOLOSEȘTE DOAR ASTA PENTRU DEBUG!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_debug_complete(ou_link, ah_link)
