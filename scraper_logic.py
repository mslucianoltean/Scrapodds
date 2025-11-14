# scraper_logic.py (VERSIUNEA DE DEBUG - CLICK PE TOATE RÂNDURILE)

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
TARGET_BOOKMAKER = "Betano" # Rămâne doar pentru referință
TYPE_ODDS = 'CLOSING' 
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM (Rămân neschimbate)
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
    """Extrage numele bookmakerului dintr-un rând bazat pe DIV (caută div[1])."""
    xpath = f'{row_xpath}/div[1]' 
    element = find_element(driver, By.XPATH, xpath)
    return element.text.strip() if element else None

def get_opening_odd(driver, xpath):
    return 'DEZACTIVAT (instabil)'

def fffi(driver, xpath):
    """Returnează cota de închidere (doar textul cotei)."""
    return ffi(driver, xpath) 

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (DEBUG - CLICK PE TOATE RÂNDURILE)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    global TARGET_BOOKMAKER 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat'
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
        wait = WebDriverWait(driver, 30)
        
        # Containerul de Rânduri (Base Rows)
        base_rows_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]'

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        time.sleep(2) 
        
        # --- HANDLE POPUP/COOKIES ---
        try:
            cookie_accept_xpath = '//*[@id="onetrust-accept-btn-handler"]'
            cookie_accept_button = find_element(driver, By.XPATH, cookie_accept_xpath)
            if cookie_accept_button:
                driver.execute_script("arguments[0].click();", cookie_accept_button)
                time.sleep(1)
        except Exception:
            pass
        # ----------------------------

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Over/Under (Containerul de cote '{base_rows_xpath}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(3) 
        
        # Extrage liniile OU (dăm click pe fiecare rând)
        for j in range(1, 10): # Limităm la primele 9 rânduri pentru viteză
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break
            
            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            # ATENȚIE: DĂM CLICK PE ORICE RÂND PENTRU A VEDEA CE SE ÎNTÂMPLĂ
            if bm_name: 
                
                ffi2(driver, row_container_xpath) 
                time.sleep(1) # Așteptăm ca datele să fie injectate
                
                # Presupunem că cotele se mută în div[2] și div[3] după click
                home_odd_xpath = f'{row_container_xpath}/div[2]' 
                away_odd_xpath = f'{row_container_xpath}/div[3]' 
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                # În loc să filtrăm, colectăm toate datele
                data = {
                    'Line': 'N/A', # Linia nu mai este esențială acum
                    'Home_Over_Close': close_home if close_home else 'N/A',
                    'Away_Under_Close': close_away if close_away else 'N/A',
                    'Bookmaker': bm_name
                }
                ou_lines.append(data)
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap (Aceeași logică)
        # ----------------------------------------------------
        driver.get(ah_link)
        time.sleep(2)
        
        # --- HANDLE POPUP/COOKIES ---
        try:
            cookie_accept_xpath = '//*[@id="onetrust-accept-btn-handler"]'
            cookie_accept_button = find_element(driver, By.XPATH, cookie_accept_xpath)
            if cookie_accept_button:
                driver.execute_script("arguments[0].click();", cookie_accept_button)
                time.sleep(1)
        except Exception:
            pass
        # ----------------------------

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Asian Handicap (Containerul de cote '{base_rows_xpath}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(3) 

        # Extrage liniile AH (dăm click pe fiecare rând)
        for j in range(1, 10): # Limităm la primele 9 rânduri pentru viteză
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break

            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name:
                
                ffi2(driver, row_container_xpath) 
                time.sleep(1) # Așteptăm ca datele să fie injectate
                
                home_odd_xpath = f'{row_container_xpath}/div[2]' 
                away_odd_xpath = f'{row_container_xpath}/div[3]' 
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                data = {
                    'Line': 'N/A',
                    'Home_Over_Close': close_home if close_home else 'N/A',
                    'Away_Under_Close': close_away if close_away else 'N/A',
                    'Bookmaker': bm_name
                }
                handicap_lines.append(data)

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
