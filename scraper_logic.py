# scraper_logic.py (VERSIUNEA 29.0 - Optimizare Timeout și Sleep)

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
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM (Rămân neschimbate)
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
        wait_short = WebDriverWait(driver, 10) 
        clickable_element = wait_short.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", clickable_element)
        return True
    except TimeoutException:
        return False 
    except Exception as e:
        return False

def get_opening_odd_from_click(driver, element_to_click_xpath):
    """Simulează click pe cota de închidere, așteaptă popup-ul și extrage cota de deschidere."""
    
    div_to_click_xpath = '/'.join(element_to_click_xpath.split('/')[:-2])
    
    if not ffi2(driver, div_to_click_xpath):
        return 'Eroare: Cota Close nu a putut fi apăsată'

    try:
        time.sleep(0.5) 
        
        popup_open_odd_xpath = '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]'
        
        # Reducere timeout așteptare popup
        wait = WebDriverWait(driver, 4) 
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
        # NOU: Mărirea timeout-ului de comandă la 180 de secunde (3 minute)
        driver = webdriver.Chrome(service=service, options=chrome_options, service_args=["--start-maximized", "--read-timeout=180"])
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului Headless. Detalii: {e}"
        return dict(results)

    # Incepe scraping-ul
    try:
        wait = WebDriverWait(driver, 30)
        
        # Punctele de referință
        LINE_ROWS_XPATH = '//div[contains(@data-testid, "collapsed-row")]' 

        # Căi interne (Rămân aceleași din V27/V28)
        HOME_ODD_REL_PATH = f'./following-sibling::div[1]//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following-sibling::div[1]/p' 
        AWAY_ODD_REL_PATH = f'./following-sibling::div[1]//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following-sibling::div[2]/p' 
        LINE_REL_PATH = './/p[contains(@class, "max-sm:!hidden")]'

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//body')))
            driver.refresh()
            time.sleep(2) 
            driver.execute_script("window.scrollTo(0, 0);")
            # REDUS: De la 8 la 5 secunde
            time.sleep(5) 
            
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))

        except:
            results['Error'] = f"Eroare: Nu s-au putut încărca liniile colapsate ('{LINE_ROWS_XPATH}') pe pagina O/U."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(2) 
        
        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)
        
        for line_row_element in all_line_rows:
            
            try:
                # 1. Dăm clic pe elementul care colapsează (line_row_element)
                driver.execute_script("arguments[0].click();", line_row_element)
                # REDUS: De la 1.5 la 1 secundă
                time.sleep(1) 
            except Exception as e:
                continue 

            try:
                # 2. Încercăm să extragem datele din rândul de detaliu deschis
                line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                # Căutarea cotei Home/Over
                home_odd_element = line_row_element.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                # Căutarea cotei Away/Under
                away_odd_element = line_row_element.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # Extragere XPath absolut pentru cota Home 
                    home_odd_xpath_full = driver.execute_script("""
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
                    """, home_odd_element)
                    
                    # Extragere XPath absolut pentru cota Away
                    away_odd_xpath_full = driver.execute_script("""
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
                    """, away_odd_element)
                    
                    # Extragerea cotelor de deschidere (folosind funcția complexă)
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath_full)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath_full)
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': "Betano (Found by Click)"
                    }
                    if data['Line'] != 'N/A':
                        ou_lines.append(data)
                        break 
                        
            except NoSuchElementException:
                pass 
            
            # 3. Curățare: Dăm clic din nou pe rând pentru a-l închide.
            try:
                driver.execute_script("arguments[0].click();", line_row_element)
                time.sleep(0.3) # Redus
            except:
                pass 
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap 
        # ----------------------------------------------------
        
        driver.get(ah_link)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//body')))
            driver.refresh()
            time.sleep(2) 
            driver.execute_script("window.scrollTo(0, 0);")
            # REDUS: De la 8 la 5 secunde
            time.sleep(5) 
            
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))
            
        except:
            results['Error_AH'] = f"Eroare: Nu s-au putut încărca liniile colapsate ('{LINE_ROWS_XPATH}') pe pagina A/H."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(2) 

        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)

        for line_row_element in all_line_rows:
            
            try:
                # 1. Dăm clic pe elementul care colapsează (line_row_element)
                driver.execute_script("arguments[0].click();", line_row_element)
                # REDUS: De la 1.5 la 1 secundă
                time.sleep(1) 
            except Exception as e:
                continue 

            try:
                # 2. Încercăm să extragem datele din rândul de detaliu deschis
                line_raw_text = ffi(line_row_element, By.XPATH, LINE_REL_PATH)
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                # Căutarea cotei Home/Over
                home_odd_element = line_row_element.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                # Căutarea cotei Away/Under
                away_odd_element = line_row_element.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # Extragere XPath absolut pentru cota Home 
                    home_odd_xpath_full = driver.execute_script("""
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
                    """, home_odd_element)
                    
                    # Extragere XPath absolut pentru cota Away
                    away_odd_xpath_full = driver.execute_script("""
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
                    """, away_odd_element)
                    
                    # Extragerea cotelor de deschidere (folosind funcția complexă)
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath_full)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath_full)

                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': "Betano (Found by Click)"
                    }
                    if data['Line'] != 'N/A':
                        handicap_lines.append(data)
                        break

            except NoSuchElementException:
                pass 
            
            # 3. Curățare: Dăm clic din nou pe rând pentru a-l închide.
            try:
                driver.execute_script("arguments[0].click();", line_row_element)
                time.sleep(0.3) # Redus
            except:
                pass 

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
