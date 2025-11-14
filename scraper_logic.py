# scraper_logic.py (VERSIUNEA FINALĂ - CU LOGICĂ DE CLICK DUBLU)

import os
import time
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
        # Folosim JavaScript pentru a forța click-ul
        driver.execute_script("arguments[0].click();", element)
        return True
    return False

def get_bookmaker_name_from_div(driver, row_xpath):
    """Extrage numele bookmakerului vizând elementul <a> din rând."""
    xpath = f'{row_xpath}//a[contains(@class, "table-main__row-content-link")]'
    element = find_element(driver, By.XPATH, xpath)
    return element.text.strip() if element else None

def fffi(driver, xpath):
    """Returnează cota de închidere (doar textul cotei)."""
    return ffi(driver, xpath) 

# NOU: Funcție pentru extragerea cotei de deschidere prin click
def get_opening_odd_from_click(driver, element_to_click_xpath):
    """Simulează click pe element, așteaptă popup-ul și extrage cota de deschidere."""
    
    # 1. Execută Click-ul pentru a deschide Popup-ul
    if not ffi2(driver, element_to_click_xpath):
        return 'Eroare: Elementul de cotă nu a putut fi apăsat'

    try:
        time.sleep(0.5) # Așteaptă scurt pentru a permite popup-ului să apară

        # 2. Extrage cota din popup (ToolTip-ul de deschidere)
        # XPath-ul generic al popup-ului de deschidere (OddsPortal)
        popup_xpath = '//*[@id="tooltip_v"]//div[contains(text(), "Opening")]/following-sibling::div'
        
        # Așteaptă scurt apariția elementului
        wait = WebDriverWait(driver, 5) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_xpath)))
        
        opening_odd_text = opening_odd_element.text.strip()
        
        # 3. Închide Popup-ul: Un al doilea click pe aceeași cotă de obicei închide popup-ul
        # sau click pe fundal (mai stabil e un al doilea click pe cotă)
        ffi2(driver, element_to_click_xpath)
        time.sleep(0.2) 
        
        return opening_odd_text

    except TimeoutException:
        # Încercăm să închidem popup-ul chiar dacă nu am găsit cota
        ffi2(driver, element_to_click_xpath)
        return 'Eroare: Popup-ul de deschidere nu a apărut (Timeout)'
    except Exception as e:
        ffi2(driver, element_to_click_xpath)
        return f'Eroare Click: {e}'

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (CU CLICK DUBLU ACTIVAT)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    global TARGET_BOOKMAKER 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver = None 

    # --- Inițializare driver (Rămâne neschimbată) ---
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
        
        base_rows_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]'
        
        # Cale relativă a cotelor (Confirmată din sesiunea anterioară)
        ODD_REL_PATH = '/div[2]/div[1]' # Div-ul care conține ambele cote
        OU_HOME_ODD_REL_PATH = '/div[2]/div[1]/div[2]' # Home/Over
        OU_AWAY_ODD_REL_PATH = '/div[2]/div[1]/div[3]' # Away/Under
        LINE_REL_PATH = '//span[contains(@class, "table-main__detail-line-more")]'

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
        
        # Extrage liniile OU 
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break
            
            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                
                # ACȚIUNE 1: DĂM CLICK PE RÂNDUL BOOKMAKER-ULUI (extinde cotele de închidere)
                ffi2(driver, row_container_xpath) 
                time.sleep(1) 
                
                # Cotele de închidere
                home_odd_xpath = row_container_xpath + OU_HOME_ODD_REL_PATH
                away_odd_xpath = row_container_xpath + OU_AWAY_ODD_REL_PATH
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 2: CLICK PE COTA DE ÎNCHIDERE PENTRU COTA DE DESCHIDERE (Popup)
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5) 
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)
                    
                    # Extrage Linia
                    line_raw_text = ffi(driver, row_container_xpath + LINE_REL_PATH)
                    line = line_raw_text.strip() if line_raw_text else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        ou_lines.append(data)
                        break 
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap
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

        # Extrage liniile AH 
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break

            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                
                # ACȚIUNE 1: DĂM CLICK PE RÂNDUL BOOKMAKER-ULUI (extinde cotele de închidere)
                ffi2(driver, row_container_xpath) 
                time.sleep(1) 
                
                # Cotele de închidere
                home_odd_xpath = row_container_xpath + OU_HOME_ODD_REL_PATH 
                away_odd_xpath = row_container_xpath + OU_AWAY_ODD_REL_PATH
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 2: CLICK PE COTA DE ÎNCHIDERE PENTRU COTA DE DESCHIDERE (Popup)
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5) 
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)

                    # Extrage Linia
                    line_raw_text = ffi(driver, row_container_xpath + LINE_REL_PATH)
                    line = line_raw_text.strip() if line_raw_text else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        handicap_lines.append(data)
                        break

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
