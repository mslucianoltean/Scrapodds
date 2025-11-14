def scrape_debug_simplu(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    
    results = {}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Doar Over/Under pentru test
        driver.get(ou_link)
        time.sleep(5)  # Așteaptă mai mult
        
        # 1. Ce titlu are pagina?
        results['Titlu'] = driver.title
        
        # 2. Ce text vede pe pagină?
        body_text = driver.find_element(By.TAG_NAME, "body").text
        results['Text_Pagina'] = body_text[:1000]  # Primele 1000 caractere
        
        # 3. Există vreun element cu "Over/Under"?
        elements_with_ou = driver.find_elements(By.XPATH, "//*[contains(text(), 'Over') or contains(text(), 'Under')]")
        results['Elemente_OverUnder'] = [elem.text for elem in elements_with_ou[:5] if elem.text]
        
        # 4. Există vreun element cu "Betano"?
        elements_betano = driver.find_elements(By.XPATH, "//*[contains(text(), 'Betano') or contains(text(), 'betano')]")
        results['Elemente_Betano'] = [elem.text for elem in elements_betano if elem.text]
        
        # 5. Ce URL este acum?
        results['URL_Curent'] = driver.current_url
        
        print("=== DEBUG COMPLETAT ===")
        
    except Exception as e:
        results['Eroare'] = str(e)
    finally:
        driver.quit()
    
    return results

# FOLOSEȘTE DOAR ASTA
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_debug_simplu(ou_link, ah_link)
