# scraper_logic.py

import os
import time
import re
import json
from collections import defaultdict
from selenium import webdriver
# Importul Service este CRUCIAL pentru Selenium 4+
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
# Bookmakerul pe care dorim să îl căutăm
TARGET_BOOKMAKER = "Betano" 
# Setați 'CLOSING' pentru a extrage Cota de Închidere ȘI Cota de Deschidere.
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
        element.click()
        return True
    return False

def get_bookmaker_name(driver, row_xpath):
    """Extrage numele bookmakerului din prima coloană a rândului (td[1])."""
    xpath = f'{row_xpath}/td[1]'
    return ffi(driver, xpath)

def get_opening_odd(driver, xpath):
    """Extrage cota de deschidere prin hover pe cota de închidere."""
    try:
        data = driver.find_element(By.XPATH, xpath)
        hov = ActionChains(driver).move_to_element(data)
        hov.perform()
        time.sleep(0.3) 
        
        data_in_the_bubble = driver.find_element(By.XPATH, "//*[@id='tooltiptext']") 
        hover_data = data_in_the_bubble.get_attribute("innerHTML")

        b = re.split('<br>', hover_data)
        c = [re.split('</strong>',y)[0] for y in b][-2] 
        opening_odd = re.split('<strong>', c)[1]
        
        return opening_odd.strip()
    except Exception:
        return 'N/A'

def fffi(driver, xpath):
    """Returnează cota (în funcție de TYPE_ODDS). Extrage cota de deschidere sau cota de închidere."""
    global TYPE_ODDS
    if TYPE_ODDS == 'OPENING':
        return get_opening_odd(driver, xpath) 
    else:
        return ffi(driver, xpath) 

def extract_odds_for_line(driver, row_xpath, home_col, away_col):
    """Extrage linia și cotele de deschidere/închidere pentru o pereche de coloane."""
    
    global TYPE_ODDS
    
    xpath_home_odd = f'{row_xpath}/td[{home_col}]/div'
    xpath_away_odd = f'{row_xpath}/td[{away_col}]/div'
    
    close_home = fffi(driver, xpath_home_odd)
    close_away = fffi(driver, xpath_away_odd)
    
    if close_home is None or close_away is None:
        return None 
        
    line_raw_text = close_home 
    line_match = re.search(r'[+-]?\d+\.?\d*', line_raw_text)
    line = line_match.group(0) if line_match else 'N/A'

    open_home = get_opening_odd(driver, xpath_home_odd) if TYPE_ODDS == 'CLOSING' else 'N/A'
    open_away = get_opening_odd(driver, xpath_away_odd) if TYPE_ODDS == 'CLOSING' else 'N/A'
    
    return {
        'Line': line,
        'Home_Over_Close': close_home,
        'Home_Over_Open': open_home,
        'Away_Under_Close': close_away,
        'Away_Under_Open': open_away,
    }

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (CU SERVICE)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(link):
    """
    Scrapează toate liniile de Over/Under și Handicap pentru un singur meci,
    filtrând pentru TARGET_BOOKMAKER, folosind driver Headless.
    """
    
    global TARGET_BOOKMAKER # Asigură-te că variabilele globale sunt disponibile
    
    results = defaultdict(dict)
    driver = None 

    # --- Configurare Headless și căi ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Căile standard de deployment
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    try:
        # **CORECTARE CHEIE:** Folosim Service() pentru a transmite calea driverului
        service = Service(chromedriver_path)
        
        driver = webdriver.Chrome(
            service=service, # Transmitem obiectul Service
            options=chrome_options
        )
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului Headless. Detalii: {e}"
        return dict(results)

    # Incepe scraping-ul
    try:
        driver.get(link)
        time.sleep(3) 

        results['Target_Bookmaker'] = TARGET_BOOKMAKER
        results['Match'] = ffi(driver, '//*[@id="col-content"]/h1')
        results['Date'] = ffi(driver, '//*[@id="col-content"]/p[1]')
        results['Final_Score'] = ffi(driver, '//*[@id="event-status"]')
        
        if not results['Match']:
            results['Error'] = "Nu s-au putut extrage detaliile meciului. Verificați link-ul."
            return dict(results)
        
        # --- Extrage cotele Over/Under (Total) ---
        total_tab_xpath = '//ul[@id="bettype-tabs"]/li[a[contains(@title, "Total")]]' 
        ou_lines = []
        if ffi2(driver, total_tab_xpath):
            time.sleep(2) 
            for j in range(1, 101):
                row_xpath = f'//*[@id="odds-data-table"]/div[1]/table/tbody/tr[{j}]'
                bm_name = get_bookmaker_name(driver, row_xpath)
                
                if bm_name and TARGET_BOOKMAKER in bm_name:
                    data = extract_odds_for_line(driver, row_xpath, home_col=2, away_col=3) 
                    if data and data['Line'] != 'N/A':
                        data['Bookmaker'] = bm_name 
                        ou_lines.append(data)
                if ffi(driver, row_xpath) is None and j > 5: break
            results['Over_Under_Lines'] = ou_lines
        else:
            results['Error_Over_Under'] = "Nu s-a putut găsi tab-ul 'Total'."
        
        # --- Extrage cotele Handicap (Asian Handicap) ---
        handicap_tab_xpath = '//ul[@id="bettype-tabs"]/li[a[contains(@title, "Asian Handicap")]]'
        handicap_lines = []
        if ffi2(driver, handicap_tab_xpath):
            time.sleep(2) 
            for j in range(1, 101):
                row_xpath = f'//*[@id="odds-data-table"]/div[1]/table/tbody/tr[{j}]'
                bm_name = get_bookmaker_name(driver, row_xpath)
                
                if bm_name and TARGET_BOOKMAKER in bm_name:
                    data = extract_odds_for_line(driver, row_xpath, home_col=2, away_col=3) 
                    if data and data['Line'] != 'N/A':
                        data['Bookmaker'] = bm_name 
                        handicap_lines.append(data)
                if ffi(driver, row_xpath) is None and j > 5: break
            results['Handicap_Lines'] = handicap_lines
        else:
            results['Error_Handicap'] = "Nu s-a putut găsi tab-ul 'Asian Handicap'."
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
