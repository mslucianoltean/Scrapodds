# scraper_logic.py (VERSIUNEA FINALĂ - CU LOGICA PE DOUĂ NIVELURI)

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
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM (Păstrăm cele mai stabile)
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
    """Dă click pe elementul de la xpath dacă există (folosind JS)."""
    element = find_element(driver, By.XPATH, xpath)
    if element:
        driver.execute_script("arguments[0].click();", element)
        return True
    return False

def get_bookmaker_name_from_row(row_element):
    """Căută textul bookmaker-ului în interiorul rândului extins."""
    try:
        # Căutăm elementul care conține textul "Betano"
        bookmaker_name_element = row_element.find_element(By.XPATH, f'.//*[contains(text(), "{TARGET_BOOKMAKER}")]')
        return bookmaker_name_element.text.strip()
    except NoSuchElementException:
        return None

def fffi(driver, xpath):
    """Returnează cota de închidere (doar textul cotei)."""
    return ffi(driver, xpath) 

def get_opening_odd_from_click(driver, element_to_click_xpath):
    """Simulează click pe cota de închidere Over, așteaptă popup-ul și extrage cota de deschidere."""
    
    if not ffi2(driver, element_to_click_xpath):
        return 'Eroare: Elementul de cotă Over nu a putut fi apăsat'

    try:
        time.sleep(0.5) 
        
        # XPath-ul OddsPortal pentru cota de deschidere (din pop-up)
        popup_xpath = '//*[@id="tooltip_v"]//div[contains(text(), "Opening")]/following-sibling::div'
        
        wait = WebDriverWait(driver, 5) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_xpath)))
        
        opening_odd_text = opening_odd_element.text.strip()
        
        # Închide Popup-ul: Dăm click pe body
        ffi2(driver, '//body') 
        time.sleep(0.2) 
        
        return opening_odd_text

    except TimeoutException:
        ffi2(driver, '//body')
        return 'Eroare: Popup-ul de deschidere nu a apărut (Timeout)'
    except Exception as e:
        ffi2(driver, '//body')
        return f'Eroare Click: {e}'

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING
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
        
        base_rows_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]'
        
        # Cale relativă a cotelor (din interiorul rândului Betano, care este un sub-element)
        # Am dedus aceste căi folosind XPath-ul complex dat de dvs.
        BETANO_ROW_REL_PATH = '//div[contains(@class, "table-main__row--details")]/div[1]/div[2]' 
        OU_HOME_ODD_REL_PATH = '/div[2]' # Over (Cota de închidere)
        OU_AWAY_ODD_REL_PATH = '/div[3]' # Under (Cota de închidere)
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
        
        # Extrage liniile OU (Căutăm linia principală)
        for j in range(1, 101):
            line_row_xpath = f'{base_rows_xpath}/div[{j}]'
            line_row_element = find_element(driver, By.XPATH, line_row_xpath)
            if not line_row_element and j > 5: break
            
            # ACȚIUNE 1: DĂM CLICK PE RÂNDUL LINIEI PENTRU A DESCHIDE BOOKMAKERII
            if ffi2(driver, line_row_xpath): 
                time.sleep(1) # Așteaptă extinderea

                try:
                    # ACȚIUNE 2: Căutăm rândul Betano în interiorul rândului Liniei
                    # Folosim o căutare relativă complexă
                    betano_row_xpath = f'{line_row_xpath}//a[contains(@class, "table-main__row-content-link") and contains(text(), "{TARGET_BOOKMAKER}")]/ancestor::div[contains(@class, "table-main__row--details-line")]'
                    betano_row_element = driver.find_element(By.XPATH, betano_row_xpath)
                    
                    # Rândul Betano a fost găsit. Extragem datele.
                    bm_name = get_bookmaker_name_from_row(betano_row_element)

                    # Cotele de închidere (relative la rândul Betano)
                    home_odd_xpath = betano_row_xpath + OU_HOME_ODD_REL_PATH
                    away_odd_xpath = betano_row_xpath + OU_AWAY_ODD_REL_PATH
                    
                    close_home = fffi(driver, home_odd_xpath) # Cota Over (Închidere)
                    close_away = fffi(driver, away_odd_xpath) # Cota Under (Închidere)
                    
                    if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                        
                        # ACȚIUNE 3: CLICK PE COTA OVER (ÎNCHIDERE) PENTRU A OBȚINE COTA DE DESCHIDERE
                        open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                        open_away = close_away # Under Close este Under Open
                        
                        # Extrage Linia din rândul părinte
                        line_raw_text = ffi(driver, line_row_xpath + LINE_REL_PATH)
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
                            
                except NoSuchElementException:
                    # Nu am găsit Betano în rândul extins. Nu facem nimic.
                    pass 
                
                # Închide rândul liniei (click din nou pe el) pentru curățenie
                ffi2(driver, line_row_xpath) 
                time.sleep(0.5) 
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap (Logică Identică)
        # ----------------------------------------------------
        
        driver.get(ah_link)
        time.sleep(2)
        
        # --- HANDLE POPUP/COOKIES --- (Skip for brevity) ---

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
            line_row_xpath = f'{base_rows_xpath}/div[{j}]'
            line_row_element = find_element(driver, By.XPATH, line_row_xpath)
            if not line_row_element and j > 5: break

            # ACȚIUNE 1: DĂM CLICK PE RÂNDUL LINIEI PENTRU A DESCHIDE BOOKMAKERII
            if ffi2(driver, line_row_xpath): 
                time.sleep(1) 

                try:
                    # ACȚIUNE 2: Căutăm rândul Betano în interiorul rândului Liniei
                    betano_row_xpath = f'{line_row_xpath}//a[contains(@class, "table-main__row-content-link") and contains(text(), "{TARGET_BOOKMAKER}")]/ancestor::div[contains(@class, "table-main__row--details-line")]'
                    betano_row_element = driver.find_element(By.XPATH, betano_row_xpath)
                    
                    bm_name = get_bookmaker_name_from_row(betano_row_element)

                    # Cotele de închidere (relative la rândul Betano)
                    home_odd_xpath = betano_row_xpath + OU_HOME_ODD_REL_PATH
                    away_odd_xpath = betano_row_xpath + OU_AWAY_ODD_REL_PATH
                    
                    close_home = fffi(driver, home_odd_xpath) # Cota Home (Închidere)
                    close_away = fffi(driver, away_odd_xpath) # Cota Away (Închidere)
                    
                    if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                        
                        # ACȚIUNE 3: CLICK PE COTA HOME (ÎNCHIDERE) PENTRU A OBȚINE COTA DE DESCHIDERE
                        open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                        open_away = close_away # Away Close este Away Open

                        # Extrage Linia
                        line_raw_text = ffi(driver, line_row_xpath + LINE_REL_PATH)
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

                except NoSuchElementException:
                    pass 
                
                # Închide rândul liniei
                ffi2(driver, line_row_xpath) 
                time.sleep(0.5) 

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
