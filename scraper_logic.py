# scraper_logic.py (REVENIM LA CE FUNCȚIONA)

import os
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    results = defaultdict(dict)
    driver = None
    
    # Configurație simplă care funcționa
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # ----------------------------------------------------
        # OVER/UNDER - METODA SIMPLĂ
        # ----------------------------------------------------
        print("=== ÎNCEPE OU ===")
        driver.get(ou_link)
        time.sleep(5)  # Așteaptă încărcarea
        
        # 1. GĂSEȘTE TAB-UL OVER/UNDER ȘI DĂ CLICK
        tab_element = driver.find_element(By.XPATH, "//div[text()='Over/Under']")
        driver.execute_script("arguments[0].click();", tab_element)
        print("✓ Click pe Over/Under tab")
        time.sleep(3)
        
        # 2. GĂSEȘTE TOATE LINIILE
        line_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'table-main__row--details-line-wrapper')]")
        print(f"Găsite {len(line_elements)} linii")
        
        ou_lines = []
        for line_element in line_elements[:3]:  # Primele 3 linii
            try:
                # Click pe linie
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                # Găsește Betano în liniile care apar
                betano_row = line_element.find_element(By.XPATH, ".//a[contains(@href, 'betano')]/ancestor::div[contains(@class, 'table-main__row--details-line')]")
                
                # Extrage linia
                line_text = betano_row.find_element(By.XPATH, ".//span[contains(@class, 'table-main__detail-line-more')]").text
                
                # Extrage cotele
                odds_elements = betano_row.find_elements(By.XPATH, ".//div[contains(@class, 'odds')]")
                home_odd = odds_elements[0].text
                away_odd = odds_elements[1].text
                
                # Extrage opening odds (dă click pe cote)
                opening_home = get_opening_odds_simple(driver, odds_elements[0])
                opening_away = get_opening_odds_simple(driver, odds_elements[1])
                
                ou_lines.append({
                    'Line': line_text,
                    'Home_Over_Close': home_odd,
                    'Home_Over_Open': opening_home,
                    'Away_Under_Close': away_odd,
                    'Away_Under_Open': opening_away,
                    'Bookmaker': 'Betano'
                })
                
                print(f"✓ Linie OU găsită: {line_text}")
                break  # O linie e suficientă
                
            except Exception as e:
                print(f"Eroare linie: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP - ACEEAȘI METODĂ
        # ----------------------------------------------------
        print("=== ÎNCEPE AH ===")
        driver.get(ah_link)
        time.sleep(5)
        
        # 1. GĂSEȘTE TAB-UL ASIAN HANDICAP
        ah_tab = driver.find_element(By.XPATH, "//div[text()='Asian Handicap']")
        driver.execute_script("arguments[0].click();", ah_tab)
        print("✓ Click pe Asian Handicap tab")
        time.sleep(3)
        
        # 2. GĂSEȘTE LINIILE AH
        ah_line_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'table-main__row--details-line-wrapper')]")
        print(f"Găsite {len(ah_line_elements)} linii AH")
        
        ah_lines = []
        for line_element in ah_line_elements[:3]:
            try:
                driver.execute_script("arguments[0].click();", line_element)
                time.sleep(2)
                
                betano_row = line_element.find_element(By.XPATH, ".//a[contains(@href, 'betano')]/ancestor::div[contains(@class, 'table-main__row--details-line')]")
                
                line_text = betano_row.find_element(By.XPATH, ".//span[contains(@class, 'table-main__detail-line-more')]").text
                
                odds_elements = betano_row.find_elements(By.XPATH, ".//div[contains(@class, 'odds')]")
                home_odd = odds_elements[0].text
                away_odd = odds_elements[1].text
                
                opening_home = get_opening_odds_simple(driver, odds_elements[0])
                opening_away = get_opening_odds_simple(driver, odds_elements[1])
                
                ah_lines.append({
                    'Line': line_text,
                    'Home_Over_Close': home_odd,
                    'Home_Over_Open': opening_home,
                    'Away_Under_Close': away_odd,
                    'Away_Under_Open': opening_away,
                    'Bookmaker': 'Betano'
                })
                
                print(f"✓ Linie AH găsită: {line_text}")
                break
                
            except Exception as e:
                print(f"Eroare linie AH: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
            
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return dict(results)

def get_opening_odds_simple(driver, odds_element):
    """Simplu - dă click pe cota și extrage din popup"""
    try:
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(1)
        
        # Găsește popup-ul cu opening odds
        popup = driver.find_element(By.XPATH, "//*[@id='tooltip_v']")
        opening_text = popup.find_element(By.XPATH, ".//p[@class='odds-text']").text
        
        # Închide popup
        driver.find_element(By.XPATH, "//body").click()
        time.sleep(0.5)
        
        return opening_text
    except:
        return 'N/A'
