
# scraper_logic.py (VERSIUNEA FINALĂ ȘI INTEGRALĂ - CU ANCORĂ REACT)

import os
import time
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
TARGET_BOOKMAKER = "Betano" 
TYPE_ODDS = 'CLOSING' 
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM 
# ------------------------------------------------------------------------------

def find_element(driver, by_method, locator):
    """Găsește un element sau returnează None/False."""
    try:
        return driver.find_element(by_method, locator)
    except NoSuchElementException:
        return None

def ffi(driver, xpath):
    """Returnează textul elementului de la xpath dacă există."""
    element = find_element(driver, By.XPATH, xpath)
    return element.text.strip() if element else None

def ffi2(driver, xpath):
    """Dă click pe elementul de la xpath dacă există."""
    element = find_element(driver, By.XPATH, xpath)
    if element:
        driver.execute_script("arguments[0].click();", element)
        return True
    return False

def get_bookmaker_name_from_div(driver, row_xpath):
    """Extrage numele bookmakerului dintr-un rând bazat pe DIV."""
    # Presupunem că numele este într-un link (<a>) în interiorul rândului (div)
    xpath = f'{row_xpath}//div[@class="table-main__row-content"]//a'
    element = find_element(driver, By.XPATH, xpath)
    return element.text.strip() if element else None


# COTE DE DESCHIDERE DEZACTIVATE PENTRU STABILITATE
def get_opening_odd(driver, xpath):
    """DEZACTIVAT: Funcția de hover care cauzează instabilitate."""
    return 'DEZACTIVAT (instabil)'

def fffi(driver, xpath):
    """Returnează cota de închidere (doar textul cotei)."""
    return ffi(driver, xpath) 

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (ADAPTATĂ LA DIVS & REACT ANCHOR)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    Scrapează liniile de Over/Under și Handicap din link-uri directe (ou_link și ah_link).
    """
    
    global TARGET_BOOKMAKER 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat' # Placeholder 
    driver = None 

    # --- Inițializare driver ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului Headless. Detalii: {e}"
        return dict(results)

    # Incepe scraping-ul
    try:
        wait = WebDriverWait(driver, 20)
        
        # ANCORA NOUĂ (React Header)
        match_title_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[1]'
        
        # Ancora pentru elementul părinte al rândurilor de cote (structura DIV)
        base_rows_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]'

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        
        try:
            # Așteaptă titlul (ancora React)
            wait.until(EC.visibility_of_element_located((By.XPATH, match_title_xpath)))
        except:
            results['Error'] = "Eroare la încărcarea paginii Over/Under (Noua ancoră React nu a fost găsită)."
            driver.quit()
            return dict(results)

        # Așteaptă containerul de rânduri
        wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        
        ou_lines = []
        time.sleep(3) 
        
        # Extrage liniile OU (rândurile sunt div[j])
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            if not find_element(driver, By.XPATH, row_container_xpath) and j > 5: break
            
            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                
                home_odd_xpath = f'{row_container_xpath}/div[1]' # Poziția Home/Over
                away_odd_xpath = f'{row_container_xpath}/div[2]' # Poziția Away/Under
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away:
                    line_raw_text = close_home 
                    line_match = re.search(r'[+-]?\d+\.?\d*', line_raw_text)
                    line = line_match.group(0) if line_match else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': 'DEZACTIVAT (instabil)',
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': 'DEZACTIVAT (instabil)',
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        ou_lines.append(data)
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap
        # ----------------------------------------------------
        driver.get(ah_link)
        
        wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        
        handicap_lines = []
        time.sleep(3) 

        # Extrage liniile AH (Aceeași logică ca la OU)
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            if not find_element(driver, By.XPATH, row_container_xpath) and j > 5: break

            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                home_odd_xpath = f'{row_container_xpath}/div[1]' 
                away_odd_xpath = f'{row_container_xpath}/div[2]' 
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away:
                    line_raw_text = close_home 
                    line_match = re.search(r'[+-]?\d+\.?\d*', line_raw_text)
                    line = line_match.group(0) if line_match else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': 'DEZACTIVAT (instabil)',
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': 'DEZACTIVAT (instabil)',
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        handicap_lines.append(data)

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
