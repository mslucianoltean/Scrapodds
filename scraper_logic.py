# scraper_logic.py (VERSIUNEA 6.0 - ÎNCĂRCARE STABILITĂ ȘI CĂUTARE ÎMBUNĂTĂȚITĂ)

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
TARGET_BOOKMAKER_HREF_PARTIAL = "betano" 
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
    """Dă click pe elementul de la xpath dacă există (folosind JS)."""
    element = find_element(driver, By.XPATH, xpath)
    if element:
        driver.execute_script("arguments[0].click();", element)
        return True
    return False

def get_opening_odd_from_click(driver, element_to_click_xpath):
    """Simulează click pe cota de închidere, așteaptă popup-ul și extrage cota de deschidere."""
    
    div_to_click_xpath = '/'.join(element_to_click_xpath.split('/')[:-2])
    
    if not ffi2(driver, div_to_click_xpath):
        return 'Eroare: Cota Close nu a putut fi apăsată'

    try:
        time.sleep(0.5) 
        
        popup_open_odd_xpath = '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]'
        
        wait = WebDriverWait(driver, 5) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_open_odd_xpath)))
        
        opening_odd_text = opening_odd_element.text.strip()
        
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
    
    global TARGET_BOOKMAKER_HREF_PARTIAL 
    
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
        
        # NOU CONTAINER PRINCIPAL DE AȘTEPTAT (Mai sus în ierarhie)
        main_container_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]'
        
        # Căi relative (din interiorul rândului Betano) - vizează direct <p>
        OU_HOME_ODD_REL_PATH = '/div[3]/div/div/p' 
        OU_AWAY_ODD_REL_PATH = '/div[4]/div/div/p' 
        
        # Căutăm rândul bookmaker-ului pe baza link-ului "betano"
        BETANO_ROW_XPATH_TEMPLATE = f'//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/ancestor::div[contains(@class, "table-main__row--details-line")]'
        
        # Extrage Linia (din rândul Părinte)
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
            # Așteptăm elementul părinte de nivel înalt
            wait.until(EC.visibility_of_element_located((By.XPATH, main_container_xpath)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Over/Under (Containerul principal '{main_container_xpath}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(3) 
        
        # Căutăm toate rândurile de cote din interiorul containerului principal (Căutare mai flexibilă)
        all_line_rows = driver.find_elements(By.XPATH, f"{main_container_xpath}//div[contains(@data-testid, 'table-main-row')]")
        
        # Iterăm prin rândurile găsite
        for line_row_element in all_line_rows:
            
            # Folosim XPath-ul absolut al elementului rând pentru click
            line_row_xpath = driver.execute_script("return arguments[0].tagName + (arguments[0].id ? '#' + arguments[0].id : '') + (arguments[0].className ? '.' + arguments[0].className.split(' ').join('.') : '');", line_row_element)
            
            # ACȚIUNE 1: DĂM CLICK PE RÂNDUL LINIEI PENTRU A DESCHIDE BOOKMAKERII
            # Trebuie să folosim o cale robustă pentru click (aici folosim elementul direct)
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1) 

            try:
                # ACȚIUNE 2: Găsim rândul Betano pe baza Link-ului, relativ la rândul liniei curente
                betano_row_element = line_row_element.find_element(By.XPATH, f'.{BETANO_ROW_XPATH_TEMPLATE}')
                
                # Extragem XPath-ul absolut al rândului Betano pentru a-l folosi la extracția cotelor
                betano_row_xpath_full = driver.execute_script("var element = arguments[0]; var xpath = ''; while (element) { var tag = element.tagName; if (!tag) break; var parent = element.parentNode; var siblings = parent.children; var count = 0; var index = 0; for (var i = 0; i < siblings.length; i++) { var sibling = siblings[i]; if (sibling.tagName === tag) { count++; if (sibling === element) { index = count; } } } var tagName = tag.toLowerCase(); var xpathIndex = index > 1 ? '[' + index + ']' : ''; xpath = '/' + tagName + xpathIndex + xpath; element = parent; } return xpath.replace('html[1]/body[1]', '/html/body');", betano_row_element)

                # Extragem numele (pentru afișare)
                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

                # Cotele de închidere XPath-uri complete
                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, home_odd_xpath) 
                close_away = ffi(driver, away_odd_xpath) 
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 3: CLICK PE COTE PENTRU COTE DE DESCHIDERE
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)
                    
                    # Extrage Linia (relativ la rândul liniei)
                    line_raw_text = line_row_element.find_element(By.XPATH, f'.{LINE_REL_PATH}').text
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
                        
                        driver.execute_script("arguments[0].click();", line_row_element) # Închide rândul
                        break 
                        
            except NoSuchElementException:
                # Rândul Betano nu a fost găsit în rândul liniei curente.
                pass 
            
            # Închide rândul liniei (click din nou pe el)
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(0.5) 
    
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap (Logică Identică)
        # ----------------------------------------------------
        
        driver.get(ah_link)
        time.sleep(2)
        
        # --- HANDLE POPUP/COOKIES --- (Omitere pentru simplitate) 

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, main_container_xpath)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Asian Handicap (Containerul principal '{main_container_xpath}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(3) 

        # Căutăm toate rândurile de cote din interiorul containerului principal
        all_line_rows = driver.find_elements(By.XPATH, f"{main_container_xpath}//div[contains(@data-testid, 'table-main-row')]")

        # Extrage liniile AH 
        for line_row_element in all_line_rows:
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1) 

            try:
                # ACȚIUNE 2: Găsim rândul Betano pe baza Link-ului, relativ la rândul liniei curente
                betano_row_element = line_row_element.find_element(By.XPATH, f'.{BETANO_ROW_XPATH_TEMPLATE}')
                
                # Extragem XPath-ul absolut al rândului Betano pentru a-l folosi la extracția cotelor
                betano_row_xpath_full = driver.execute_script("var element = arguments[0]; var xpath = ''; while (element) { var tag = element.tagName; if (!tag) break; var parent = element.parentNode; var siblings = parent.children; var count = 0; var index = 0; for (var i = 0; i < siblings.length; i++) { var sibling = siblings[i]; if (sibling.tagName === tag) { count++; if (sibling === element) { index = count; } } } var tagName = tag.toLowerCase(); var xpathIndex = index > 1 ? '[' + index + ']' : ''; xpath = '/' + tagName + xpathIndex + xpath; element = parent; } return xpath.replace('html[1]/body[1]', '/html/body');", betano_row_element)


                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

                # Cotele de închidere
                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, home_odd_xpath)
                close_away = ffi(driver, away_odd_xpath)
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 3: CLICK PE COTE PENTRU COTE DE DESCHIDERE
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)

                    # Extrage Linia
                    line_raw_text = line_row_element.find_element(By.XPATH, f'.{LINE_REL_PATH}').text
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
                        
                        driver.execute_script("arguments[0].click();", line_row_element)
                        break

            except NoSuchElementException:
                pass 
            
            # Închide rândul liniei
            driver.execute_script("arguments[0].click();", line_row_element) 
            time.sleep(0.5) 

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
