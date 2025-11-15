# scraper_logic.py (VERSIUNEA 33.0 - Clic pe Elementul Text al Liniei)

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
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului Headless. Detalii: {e}"
        return dict(results)

    # Incepe scraping-ul
    try:
        driver.set_script_timeout(180) 
        wait = WebDriverWait(driver, 30)
        
        # Punctele de referință
        LINE_ROWS_XPATH = '//div[contains(@data-testid, "collapsed-row")]' 
        LINE_CLICK_REL_PATH = './/p[contains(@class, "max-sm:!hidden")]' # NOU: Elementul pe care dăm clic

        # Căi interne (din V29.0)
        HOME_ODD_REL_PATH = f'./following-sibling::div[1]//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following-sibling::div[1]/p' 
        AWAY_ODD_REL_PATH = f'./following-sibling::div[1]//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following-sibling::div[2]/p' 
        LINE_REL_PATH = LINE_CLICK_REL_PATH # Linia de extragere e aceeași ca linia de clic

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//body')))
            driver.refresh()
            time.sleep(2) 
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(5) 
            
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))

        except:
            results['Error'] = f"Eroare: Nu s-au putut încărca liniile colapsate ('{LINE_ROWS_XPATH}') pe pagina O/U."
            driver.quit()
            return dict(results)
        
        ou_lines = []
        time.sleep(2) 
        
        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)
        html_ou_dumped = False 
        
        for line_row_element in all_line_rows:
            
            try:
                # Găsim elementul p din interiorul rândului (rândul care se colapsează)
                element_to_click = line_row_element.find_element(By.XPATH, LINE_CLICK_REL_PATH)
                
                # 1. Dăm clic pe elementul interior (element_to_click)
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(1.5) # Timp de așteptare puțin mai mare
                
                # **!!! DEBUG: DUMP HTML DUPĂ CLIC !!!**
                if not html_ou_dumped:
                    # Extrage întregul cod sursă al paginii
                    results['Debug_HTML_OU'] = driver.page_source 
                    html_ou_dumped = True
                
            except Exception as e:
                continue 

            try:
                # 2. Încercăm să extragem datele din rândul de detaliu deschis
                line_raw_text = element_to_click.text.strip() # Extragem textul direct din elementul pe care am dat clic
                line = line_raw_text if line_raw_text else 'N/A'
                
                # Căutarea cotei Home/Over
                home_odd_element = line_row_element.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                # Căutarea cotei Away/Under
                away_odd_element = line_row_element.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # Extragere XPath absolut pentru cota Home/Away
                    home_odd_xpath_full = driver.execute_script("""...""", home_odd_element)
                    away_odd_xpath_full = driver.execute_script("""...""", away_odd_element)
                    
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
            
            # 3. Curățare: Dăm clic din nou pe elementul interior pentru a-l închide.
            try:
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(0.3) 
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
            time.sleep(5) 
            
            wait.until(EC.visibility_of_element_located((By.XPATH, LINE_ROWS_XPATH)))
            
        except:
            results['Error_AH'] = f"Eroare: Nu s-au putut încărca liniile colapsate ('{LINE_ROWS_XPATH}') pe pagina A/H."
            driver.quit()
            return dict(results)
        
        handicap_lines = []
        time.sleep(2) 

        all_line_rows = driver.find_elements(By.XPATH, LINE_ROWS_XPATH)
        html_ah_dumped = False 

        for line_row_element in all_line_rows:
            
            try:
                # Găsim elementul p din interiorul rândului (rândul care se colapsează)
                element_to_click = line_row_element.find_element(By.XPATH, LINE_CLICK_REL_PATH)
                
                # 1. Dăm clic pe elementul interior (element_to_click)
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(1.5) 
                
                # **!!! DEBUG: DUMP HTML DUPĂ CLIC !!!**
                if not html_ah_dumped:
                    results['Debug_HTML_AH'] = driver.page_source
                    html_ah_dumped = True

            except Exception as e:
                continue 

            try:
                # 2. Încercăm să extragem datele din rândul de detaliu deschis
                line_raw_text = element_to_click.text.strip()
                line = line_raw_text if line_raw_text else 'N/A'
                
                # Căutarea cotei Home/Over
                home_odd_element = line_row_element.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                # Căutarea cotei Away/Under
                away_odd_element = line_row_element.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    # Extragere XPath absolut pentru cota Home/Away
                    home_odd_xpath_full = driver.execute_script("""...""", home_odd_element)
                    away_odd_xpath_full = driver.execute_script("""...""", away_odd_element)
                    
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
            
            # 3. Curățare: Dăm clic din nou pe elementul interior pentru a-l închide.
            try:
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(0.3) 
            except:
                pass 

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
