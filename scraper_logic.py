def scrape_via_direct_urls(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import os
    import time
    import re
    
    results = {'Match': 'Scraping via URL-uri directe'}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # OVER/UNDER
        print("=== PORNIM CU OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(5)
        
        # Pas 1: Extrage liniile
        line_values = extract_ou_lines(driver)
        print(f"Linii extrase: {line_values}")
        
        # Pas 2: Construiește URL-uri
        base_url = ou_link.split('#')[0]
        urls_to_scrape = build_direct_urls(base_url, line_values)
        
        # Pas 3: Extrage cotele pentru fiecare URL
        ou_lines = []
        for url_info in urls_to_scrape[:3]:  # Testează primele 3
            odds_data = extract_betano_odds(driver, url_info)
            if odds_data:
                ou_lines.append(odds_data)
        
        results['Over_Under_Lines'] = ou_lines
        
        # ASIAN HANDICAP (același logică)
        # ... (poți să adaugi mai târziu)
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'all_line_values': line_values
        }
        
    except Exception as e:
        results['Error'] = str(e)
    finally:
        driver.quit()
    
    return results
