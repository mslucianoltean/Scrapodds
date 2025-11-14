# scraper_logic.py (VERSIUNEA 19.0 - Clic Direct pe Textul Tabului)

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
    try:
        # Așteptăm elementul să fie click-uibil
        wait_short = WebDriverWait(driver, 10) # Așteptare mai lungă de 10s pentru tab
        clickable_element = wait_short.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", clickable_element)
        return True
    except TimeoutException:
        return False # Returnăm False dacă nu e găsit/click-uibil în 10s
    except Exception:
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
    chrome_options.add_argument("--window-size=1920,1080") 
    
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
        
        # Punctele de referință
        OU_DIV_TEXT_XPATH = "//div[text()='Over/Under']" # Target direct pe div-ul cu textul
        AH_DIV_TEXT_XPATH = "//div[text()='Asian Handicap']" # Target direct pe div-ul cu textul
        LINE_ROWS_XPATH = '//div[contains(@class, "table-main__row--details-line-wrapper")]'

        # Căi interne
        OU_HOME_ODD_REL_PATH = '/div[3]/div/div/p' 
        OU_AWAY_ODD_REL_PATH = '/div[4]/div/div/p' 
        BETANO_ROW_REL_XPATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/ancestor::div[contains(@class, "table-main__row--details-line")]'
        LINE_REL_PATH = './/span[contains(@class, "table-main__detail-line-more")]'

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        
        # ACȚIUNE 1: Așteptăm body-ul și facem refresh
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//body')))
            driver.refresh()
            time.sleep(3) 
            
            # ACȚIUNE 2: Clic pe tabul Over/Under pentru a forța încărcarea liniilor
            if not ffi2(driver, OU_DIV_TEXT_XPATH):
                 results['Error'] = f"Eroare: Nu a putut fi găsit/apăsat tabul Over/Under ('{OU_DIV_TEXT_XPATH}')."
                 driver.quit()
                 return dict(results)
                 
            time.sleep(2) # Așteptăm după clic
            
            # ACȚIUNE 3: Așteptăm liniile de cote
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))

        except:
            results['Error'] = f"Eroare la încărcarea paginii Over/Under (Eșec în a găsi liniile de cote '{LINE_ROWS_XPATH}' după clic pe tabul OU)."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(3) 
        
        # Căutăm toate rândurile de linii de cote (elemente)
        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)
        
        # Iterăm prin rândurile găsite și extragem cotele
        for line_row_element in all_line_rows:
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1.5) 

            try:
                betano_row_element = line_row_element.find_element(By.XPATH, BETANO_ROW_REL_XPATH)
                
                line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

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


                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, By.XPATH, home_odd_xpath) 
                close_away = ffi(driver, By.XPATH, away_odd_xpath) 
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)
                    
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
                        
                        driver.execute_script("arguments[0].click();", line_row_element)
                        break 
                        
            except NoSuchElementException:
                pass 
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(0.5) 
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap 
        # ----------------------------------------------------
        
        driver.get(ah_link)
        
        # ACȚIUNE 1: Așteptăm body-ul și facem refresh
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//body')))
            driver.refresh()
            time.sleep(3) 
            
            # ACȚIUNE 2: Clic pe tabul Asian Handicap
            if not ffi2(driver, AH_DIV_TEXT_XPATH):
                 results['Error_AH'] = f"Eroare: Nu a putut fi găsit/apăsat tabul Asian Handicap ('{AH_DIV_TEXT_XPATH}')."
                 driver.quit()
                 return dict(results)
                 
            time.sleep(2) 
            
            # ACȚIUNE 3: Așteptăm liniile de cote
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))
            
        except:
            results['Error_AH'] = f"Eroare la încărcarea paginii Asian Handicap (Nicio linie de cote '{LINE_ROWS_XPATH}' nu a fost găsită în 30s după clic pe tabul AH)."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(3) 

        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)

        # Extrage liniile AH 
        for line_row_element in all_line_rows:
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(1.5) 

            try:
                betano_row_element = line_row_element.find_element(By.XPATH, BETANO_ROW_REL_XPATH)
                
                line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                bm_name_element = betano_row_element.find_element(By.XPATH, f'.//p[contains(text(), "Betano")]')
                bm_name = bm_name_element.text.strip() if bm_name_element else "Betano.ro"

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


                home_odd_xpath = betano_row_xpath_full + OU_HOME_ODD_REL_PATH
                away_odd_xpath = betano_row_xpath_full + OU_AWAY_ODD_REL_PATH
                
                close_home = ffi(driver, By.XPATH, home_odd_xpath)
                close_away = ffi(driver, By.XPATH, away_odd_xpath)
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath)

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
            
            driver.execute_script("arguments[0].click();", line_row_element)
            time.sleep(0.5) 

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
