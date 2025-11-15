# scraper_logic.py (VERSIUNEA 41.0 - AȘTEPTARE EXPLICITĂ + EXTRACȚIE LINIe)

import os
import time
import re 
from collections import defaultdict 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.remote.webelement import WebElement
from typing import Optional, Dict, Any, List

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
TARGET_BOOKMAKER_HREF_PARTIAL = "betano" 
BASE_URL_TEMPLATE = "https://www.oddsportal.com/basketball/usa/nba/{match_slug}/#over-under;1;{line_value:.2f};0"
BASE_URL_AH_TEMPLATE = "https://www.oddsportal.com/basketball/usa/nba/{match_slug}/#ah;1;{line_value:.2f};0"
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM ȘI PARSARE
# ------------------------------------------------------------------------------

def wait_for_collapsed_rows(driver: webdriver.Chrome, ou_or_ah_link: str, ou_or_ah_testid: str) -> bool:
    """Așteaptă până când elementele colapsate sunt vizibile și navighează."""
    
    driver.get(ou_or_ah_link)
    # Caută un element din rândurile colapsate O/U sau AH
    wait_xpath = f'//div[@data-testid="{ou_or_ah_testid}"]'
    
    try:
        wait = WebDriverWait(driver, 20) 
        wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
        time.sleep(3) # Pauză de siguranță după ce elementul apare
        return True
    except TimeoutException:
        return False

def extract_line_value(line_text: str) -> Optional[float]:
    """Extrage valoarea numerică a liniei (ex: 'Over/Under +216.5' -> 216.5)."""
    # Regex mai permisiv, caută număr cu sau fără punct, precedat opțional de +/-
    match = re.search(r'[\+\-]?(\d+\.?\d*)', line_text)
    if match:
        return float(match.group(1)) 
    return None

def get_match_slug(url: str) -> Optional[str]:
    """Extrage slug-ul meciului (ex: phoenix-suns-indiana-pacers-KtP8YyZj) din URL-ul de bază."""
    match = re.search(r'/[^/]+/[^/]+/([^/]+)/#', url)
    if match:
        return match.group(1)
    return None

def ffi2(driver: webdriver.Chrome, xpath: str) -> bool:
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

def get_opening_odd_from_click(driver: webdriver.Chrome, element_to_click: WebElement) -> str:
    """Simulează click pe cota de închidere, așteaptă popup-ul și extrage cota de deschidere."""
    
    # 2. Clic pe cota de închidere pentru a deschide popup-ul
    try:
        driver.execute_script("arguments[0].click();", element_to_click)
    except Exception as e:
        return f'Eroare: Cota Close nu a putut fi apăsată: {e}'

    # 3. Extragerea cotei Open din popup
    try:
        time.sleep(0.5) 
        # XPath al cotei Open în popup (din inspectarea anterioară)
        popup_open_odd_xpath = '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]' 
        
        wait = WebDriverWait(driver, 4) 
        opening_odd_element = wait.until(EC.presence_of_element_located((By.XPATH, popup_open_odd_xpath)))
        
        opening_odd_text = opening_odd_element.text.strip()
        
        # Clic pe <body> pentru a închide popup-ul
        ffi2(driver, '//body') 
        time.sleep(0.2) 
        
        return opening_odd_text

    except TimeoutException:
        ffi2(driver, '//body')
        return 'Eroare: Popup-ul de deschidere nu a apărut (Timeout)'
    except Exception as e:
        ffi2(driver, '//body')
        return f'Eroare Click/Extracție Popup: {e}'


# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link: str, ah_link: str) -> Dict[str, Any]:
    
    global TARGET_BOOKMAKER_HREF_PARTIAL
    
    results: Dict[str, Any] = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver: Optional[webdriver.Chrome] = None 
    
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
        
        # Punctele de referință
        COLLAPSED_ROW_XPATH_OU = '//div[@data-testid="over-under-collapsed-row"]'
        LINE_TEXT_REL_XPATH = './/p[contains(@class, "!hidden") and contains(text(), "+")]'
        
        EXPANDED_ROW_STATIC_XPATH_OU = '//div[@data-testid="over-under-expanded-row"]'
        EXPANDED_ROW_STATIC_XPATH_AH = '//div[@data-testid="asian-handicap-expanded-row"]'
        
        HOME_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][1]//p[@class="odds-text"]' 
        AWAY_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][2]//p[@class="odds-text"]' 
        
        # Extragerea slug-ului meciului din URL-ul inițial
        match_slug = get_match_slug(ou_link)
        if not match_slug:
            results['Error'] = "Eroare la extragerea slug-ului meciului din URL."
            driver.quit()
            return dict(results)

        # ----------------------------------------------------
        # ETAPA 1: Extrage liniile Over/Under (generare URL-uri)
        # ----------------------------------------------------
        if wait_for_collapsed_rows(driver, ou_link, "over-under-collapsed-row"):
            # 1. Extrage toate valorile de linie disponibile
            line_rows: List[WebElement] = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_OU)
            line_values: set[float] = set()
            
            for row in line_rows:
                try:
                    line_text_element = row.find_element(By.XPATH, LINE_TEXT_REL_XPATH)
                    value = extract_line_value(line_text_element.text.strip())
                    if value is not None:
                        line_values.add(value)
                except NoSuchElementException:
                    continue # Sări peste rândul care nu are textul de linie așteptat
            
            if not line_values:
                results['Over_Under_Lines'] = "Nu au fost găsite valori de linii O/U."
            
            ou_lines: List[Dict[str, Any]] = []
            
            # 2. Parcurge fiecare linie (URL) nou generată
            for line_value in sorted(list(line_values)):
                new_url = BASE_URL_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
                
                driver.get(new_url)
                time.sleep(3) # Așteptăm încărcarea paginii specifice liniei

                try:
                    # 3. Extragerea directă a cotelor din rândul deja expandat
                    expanded_row = driver.find_element(By.XPATH, EXPANDED_ROW_STATIC_XPATH_OU)
                    
                    home_odd_element = expanded_row.find_element(By.XPATH, HOME_ODD_REL_PATH)
                    close_home = home_odd_element.text.strip()
                    
                    away_odd_element = expanded_row.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                    close_away = away_odd_element.text.strip()
                    
                    # Verificăm dacă Betano are cotă
                    if close_home and close_away and close_home not in ['N/A', '-', ''] and close_away not in ['N/A', '-', '']:
                        
                        # Logica pentru cota Open
                        open_home = get_opening_odd_from_click(driver, home_odd_element)
                        time.sleep(0.5)
                        open_away = get_opening_odd_from_click(driver, away_odd_element)
                        
                        data = {
                            'Line': line_value,
                            'Home_Over_Close': close_home,
                            'Home_Over_Open': open_home,
                            'Away_Under_Close': close_away,
                            'Away_Under_Open': open_away,
                            'Bookmaker': "Betano (Static URL)"
                        }
                        ou_lines.append(data)

                except NoSuchElementException:
                    pass # Betano nu este prezent în acest rând
                except Exception:
                    pass
            
            results['Over_Under_Lines'] = ou_lines
        else:
            results['Over_Under_Lines'] = "Eroare: Nu s-au putut încărca rândurile O/U în timpul alocat."


        # ----------------------------------------------------
        # ETAPA 2: Extrage liniile Handicap (Logica identică)
        # ----------------------------------------------------
        
        if wait_for_collapsed_rows(driver, ah_link, "over-under-collapsed-row"):
            # Notă: Probabil că data-testid este diferit pentru AH, dar testăm cu același, apoi corectăm.
            # Presupunem momentan că rândul colapsat AH are același testid: "over-under-collapsed-row"
            
            COLLAPSED_ROW_XPATH_AH = '//div[@data-testid="over-under-collapsed-row"]'
            
            # 1. Extrage toate valorile de linie disponibile pentru Handicap
            line_rows_ah: List[WebElement] = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_AH)
            line_values_ah: set[float] = set()
            
            for row in line_rows_ah:
                try:
                    line_text_element = row.find_element(By.XPATH, LINE_TEXT_REL_XPATH)
                    value = extract_line_value(line_text_element.text.strip())
                    if value is not None:
                        line_values_ah.add(value)
                except NoSuchElementException:
                    continue
            
            if not line_values_ah:
                 results['Handicap_Lines'] = "Nu au fost găsite valori de linii AH."

            handicap_lines: List[Dict[str, Any]] = []

            # 2. Parcurge fiecare linie (URL) nou generată
            for line_value in sorted(list(line_values_ah)):
                new_url = BASE_URL_AH_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
                
                driver.get(new_url)
                time.sleep(3) 
                
                try:
                    # 3. Extragerea directă a cotelor din rândul deja expandat
                    expanded_row = driver.find_element(By.XPATH, EXPANDED_ROW_STATIC_XPATH_AH)
                    
                    home_odd_element = expanded_row.find_element(By.XPATH, HOME_ODD_REL_PATH)
                    close_home = home_odd_element.text.strip()
                    
                    away_odd_element = expanded_row.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                    close_away = away_odd_element.text.strip()
                    
                    if close_home and close_away and close_home not in ['N/A', '-', ''] and close_away not in ['N/A', '-', '']:
                        
                        open_home = get_opening_odd_from_click(driver, home_odd_element)
                        time.sleep(0.5)
                        open_away = get_opening_odd_from_click(driver, away_odd_element)
                        
                        data = {
                            'Line': line_value,
                            'Home_Handicap_Close': close_home,
                            'Home_Handicap_Open': open_home,
                            'Away_Handicap_Close': close_away,
                            'Away_Handicap_Open': open_away,
                            'Bookmaker': "Betano (Static URL)"
                        }
                        handicap_lines.append(data)

                except NoSuchElementException:
                    pass 
                except Exception:
                    pass

            results['Handicap_Lines'] = handicap_lines
        else:
            results['Handicap_Lines'] = "Eroare: Nu s-au putut încărca rândurile AH în timpul alocat."
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
