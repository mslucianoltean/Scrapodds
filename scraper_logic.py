import os
import time
from collections import defaultdict # Linia critică adăugată pentru a rezolva eroarea
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.remote.webelement import WebElement

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
# Identificator robust bazat pe atributul href al link-ului Betano
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

def get_opening_odd_from_click(driver: webdriver.Chrome, element_to_click: WebElement):
    """Simulează click pe cota de închidere, așteaptă popup-ul și extrage cota de deschidere."""
    
    # Obținem XPath-ul absolut al elementului WebElement dat, pentru a putea da clic pe el.
    try:
        # Scriptul JS pentru a obține XPath-ul absolut
        get_xpath_script = """
        function getXPath(element) {
            if (element.id !== '')
                return '//*[@id="' + element.id + '"]';
            if (element === document.body)
                return '/html/' + element.tagName.toLowerCase();

            var ix = 0;
            var siblings = element.parentNode.childNodes;
            for (var i = 0; i < siblings.length; i++) {
                var sibling = siblings[i];
                if (sibling === element)
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                    ix++;
            }
        }
        return getXPath(arguments[0]);
        """
        element_xpath_full = driver.execute_script(get_xpath_script, element_to_click)
        
    except Exception as e:
        return f'Eroare: Nu s-a putut genera XPath: {e}'

    # Clic pe cota de închidere (element_to_click) pentru a deschide popup-ul
    try:
        driver.execute_script("arguments[0].click();", element_to_click)
    except Exception as e:
        return f'Eroare: Cota Close nu a putut fi apăsată: {e}'

    try:
        time.sleep(0.5) 
        
        # Calea XPath a cotei de deschidere din popup-ul comun (presupunem că ID-ul este stabil)
        popup_open_odd_xpath = '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]'
        
        wait = WebDriverWait(driver, 4) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_open_odd_xpath)))
        
        opening_odd_text = opening_odd_element.text.strip()
        
        # Clic pe <body> pentru a închide popup-ul
        ffi2(driver, '//body') 
        time.sleep(0.2) 
        
        return opening_odd_text

    except TimeoutException:
        # Clic pe <body> pentru a închide popup-ul, dacă e deschis
        ffi2(driver, '//body')
        return 'Eroare: Popup-ul de deschidere nu a apărut (Timeout)'
    except Exception as e:
        # Clic pe <body> pentru a închide popup-ul
        ffi2(driver, '//body')
        return f'Eroare Click/Extracție Popup: {e}'


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
        LINE_CLICK_REL_PATH = './/p[contains(@class, "max-sm:!hidden")]' # Elementul pe care dăm clic (Over/Under +X.X)

        # Căi interne (UPDATE 37.0 - XPath simplificat)
        
        # 1. Găsim rândul expandat
        EXPANDED_ROW_XPATH = './following-sibling::div[1]//div[@data-testid="over-under-expanded-row"]'
        
        # 2. Căutăm cotele Betano (utilizând EXPANDED_ROW ca bază)
        # HOME_ODD_REL_PATH: Navighează de la link-ul Betano la cota Over (primul odd-container)
        HOME_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][1]//p[@class="odds-text"]' 
        
        # AWAY_ODD_REL_PATH: Navighează de la link-ul Betano la cota Under (al doilea odd-container)
        AWAY_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][2]//p[@class="odds-text"]' 
        
        LINE_REL_PATH = LINE_CLICK_REL_PATH 

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
        
        for line_row_element in all_line_rows:
            
            try:
                element_to_click = line_row_element.find_element(By.XPATH, LINE_CLICK_REL_PATH)
                # 1. Dăm clic pe elementul interior (clicul funcționează)
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(1.5) 
                
            except Exception as e:
                continue 

            try:
                # Găsim rândul expandat care conține bookmakerii
                expanded_row = line_row_element.find_element(By.XPATH, EXPANDED_ROW_XPATH)
                
                # 2. Încercăm să extragem datele
                line_raw_text = element_to_click.text.strip()
                line = line_raw_text if line_raw_text else 'N/A'
                
                # Căutarea cotei Home/Over (in interiorul expanded_row)
                home_odd_element = expanded_row.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                # Căutarea cotei Away/Under (in interiorul expanded_row)
                away_odd_element = expanded_row.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A' and close_home != '-' and close_away != '-':
                    
                    # Extragerea cotelor de deschidere (folosind funcția complexă)
                    open_home = get_opening_odd_from_click(driver, home_odd_element)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_element)
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': "Betano (Found by HREF)"
                    }
                    if data['Line'] != 'N/A':
                        ou_lines.append(data)
                        break # Extragem doar prima linie Over/Under
                        
            except NoSuchElementException as e:
                pass # Nu am găsit elementul Betano în rândul expandat
            
            # 3. Curățare: Dăm clic din nou pe elementul interior pentru a-l închide.
            try:
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(0.3) 
            except:
                pass 
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap (Logica identică)
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

        for line_row_element in all_line_rows:
            
            try:
                element_to_click = line_row_element.find_element(By.XPATH, LINE_CLICK_REL_PATH)
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(1.5) 
                
            except Exception as e:
                continue 

            try:
                expanded_row = line_row_element.find_element(By.XPATH, EXPANDED_ROW_XPATH)
                
                line_raw_text = element_to_click.text.strip()
                line = line_raw_text if line_raw_text else 'N/A'
                
                home_odd_element = expanded_row.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                away_odd_element = expanded_row.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A' and close_home != '-' and close_away != '-':
                    
                    open_home = get_opening_odd_from_click(driver, home_odd_element)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_element)

                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': open_home,
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': open_away,
                        'Bookmaker': "Betano (Found by HREF)"
                    }
                    if data['Line'] != 'N/A':
                        handicap_lines.append(data)
                        break

            except NoSuchElementException as e:
                pass 
            
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

# ------------------------------------------------------------------------------
# ⚠️ Notă: Asigură-te că funcția principală este apelată corect în Streamlit/mediul tău.
# ------------------------------------------------------------------------------
