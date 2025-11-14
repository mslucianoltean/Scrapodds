# scraper_logic.py (VERSIUNEA 7.0 - AȘTEPTARE PE CLASĂ ȘI LOGICĂ RE-SIMPLIFICATĂ)

import os
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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

def ffi(element_or_driver, by_method, locator):
    """Returnează textul elementului de la locator dacă există. Lucrează cu Driver sau Element."""
    try:
        element = element_or_driver.find_element(by_method, locator)
        return element.text.strip()
    except NoSuchElementException:
        return None

def ffi2(driver, xpath):
    """Dă click pe elementul de la xpath dacă există (folosind JS)."""
    element = find_element(driver, By.XPATH, xpath)
    if element:
        driver.execute_script("arguments[0].click();", element)
        return True
    return False

def get_opening_odd_from_click(driver, element_to_click_xpath):
    """Simulează click pe cota de închidere, așteaptă popup-ul și extrage cota de deschidere."""
    
    # Tăiem '/div/p' pentru a obține XPath-ul div-ului care trebuie apăsat (e.g., div[3] sau div[4])
    div_to_click_xpath = '/'.join(element_to_click_xpath.split('/')[:-2])
    
    if not ffi2(driver, div_to_click_xpath):
        return 'Eroare: Cota Close nu a putut fi apăsată'

    try:
        time.sleep(0.5) 
        
        # XPath-ul pentru cota de deschidere din pop-up
        popup_open_odd_xpath = '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]'
        
        wait = WebDriverWait(driver, 5) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_open_odd_xpath)))
        
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
    
    global TARGET_BOOKMAKER_HREF_PARTIAL 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver = None 
    
    # --- Inițializare driver (rămâne standard) ---
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
        
        # Element generic de așteptat pentru a confirma încărcarea paginii
        LOADING_WAIT_XPATH = '//div[contains(@class, "table-main")]'
        
        # Căi relative (din interiorul rândului Betano) - vizează direct <p>
        OU_HOME_ODD_REL_PATH = '/div[3]/div/div/p' 
        OU_AWAY_ODD_REL_PATH = '/div[4]/div/div/p' 
        
        # Căutăm rândul bookmaker-ului pe baza link-ului "betano"
        BETANO_ROW_REL_XPATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/ancestor::div[contains(@class, "table-main__row--details-line")]'
        
        # Extrage Linia (din rândul Părinte)
        LINE_REL_PATH = './/span[contains(@class, "table-main__detail-line-more")]'
        
        # Căutăm toate rândurile de linii de cote
        LINE_ROWS_XPATH = '//div[contains(@data-testid, "table-main-row")]'

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
        
        # Așteptăm elementul general de încărcare
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, LOADING_WAIT_XPATH)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Over/Under (Elementul principal '{LOADING_WAIT_XPATH}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(3) 
        
        # Căutăm toate rândurile de linii de cote (elemente)
        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)
        
        # Iterăm prin rândurile găsite
        for line_row_element in all_line_rows:
            
            # ACȚIUNE 1: DĂM CLICK PE RÂNDUL LINIEI PENTRU A DESCHIDE BOOKMAKERII
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1) 

            try:
                # ACȚIUNE 2: Găsim rândul Betano pe baza Link-ului, relativ la rândul liniei curente
                betano_row_element = line_row_element.find_element(By.XPATH, BETANO_ROW_REL_XPATH)
                
                # Extragem numele (pentru afișare)
                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

                # Extragem XPath-ul absolut (sau un locator stabil) al rândului Betano pentru a construi cotele
                # Vom folosi XPath-ul absolut al rândului Betano pentru a extrage cotele de închidere
                # (Re-construim XPath-ul absolut al elementului Betano găsit)
                betano_row_xpath_full = driver.execute_script("""
                    var element = arguments[0]; 
                    var xpath = ''; 
                    while (element && element.parentNode && element.tagName !== 'BODY') { 
                        var tag = element.tagName;
                        var parent = element.parentNode; 
                        var siblings = parent.children; 
                        var count = 0; 
                        var index = 0; 
                        for (var i = 0; i < siblings.length; i++) { 
                            var sibling = siblings[i]; 
                            if (sibling.tagName === tag) { 
                                count++; 
                                if (sibling === element) { index = count; } 
                            } 
                        } 
                        var tagName = tag.toLowerCase(); 
                        var xpathIndex = index > 1 ? '[' + index + ']' : ''; 
                        xpath = '/' + tagName + xpathIndex + xpath; 
                        element = parent; 
                    } 
                    return '//body' + xpath;
                """, betano_row_element)


                # Cotele de închidere XPath-uri complete
                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, By.XPATH, home_odd_xpath) 
                close_away = ffi(driver, By.XPATH, away_odd_xpath) 
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 3: CLICK PE COTE PENTRU COTE DE DESCHIDERE
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)
                    
                    # Extrage Linia (relativ la rândul liniei)
                    line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
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
        
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, LOADING_WAIT_XPATH)))
        except:
            results['Error'] = f"Eroare la încărcarea paginii Asian Handicap (Elementul principal '{LOADING_WAIT_XPATH}' nu a fost găsit în 30s)."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(3) 

        # Căutăm toate rândurile de cote din interiorul containerului principal
        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)

        # Extrage liniile AH 
        for line_row_element in all_line_rows:
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1) 

            try:
                # ACȚIUNE 2: Găsim rândul Betano pe baza Link-ului, relativ la rândul liniei curente
                betano_row_element = line_row_element.find_element(By.XPATH, BETANO_ROW_REL_XPATH)
                
                # Extragem numele (pentru afișare)
                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

                # Extragem XPath-ul absolut al rândului Betano pentru a-l folosi la extracția cotelor
                betano_row_xpath_full = driver.execute_script("""
                    var element = arguments[0]; 
                    var xpath = ''; 
                    while (element && element.parentNode && element.tagName !== 'BODY') { 
                        var tag = element.tagName;
                        var parent = element.parentNode; 
                        var siblings = parent.children; 
                        var count = 0; 
                        var index = 0; 
                        for (var i = 0; i < siblings.length; i++) { 
                            var sibling = siblings[i]; 
                            if (sibling.tagName === tag) { 
                                count++; 
                                if (sibling === element) { index = count; } 
                            } 
                        } 
                        var tagName = tag.toLowerCase(); 
                        var xpathIndex = index > 1 ? '[' + index + ']' : ''; 
                        xpath = '/' + tagName + xpathIndex + xpath; 
                        element = parent; 
                    } 
                    return '//body' + xpath;
                """, betano_row_element)


                # Cotele de închidere
                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, By.XPATH, home_odd_xpath)
                close_away = ffi(driver, By.XPATH, away_odd_xpath)
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # ACȚIUNE 3: CLICK PE COTE PENTRU COTE DE DESCHIDERE
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)

                    # Extrage Linia
                    line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
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
