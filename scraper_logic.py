# scraper_logic.py (VERSIUNEA 46.0 - CORECȚIE ANTI-DETECTARE)

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
# User-Agent-ul care simulează Chrome pe Windows 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM ȘI PARSARE (Păstrăm V44.0)
# ------------------------------------------------------------------------------

def wait_for_collapsed_rows(driver: webdriver.Chrome, ou_or_ah_link: str, ou_or_ah_testid: str) -> bool:
    """Navighează și așteaptă până când rândurile colapsate sunt vizibile."""
    
    driver.get(ou_or_ah_link)
    wait_xpath = f'//div[@data-testid="{ou_or_ah_testid}"]'
    
    try:
        wait = WebDriverWait(driver, 20) 
        wait.until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
        time.sleep(3) 
        return True
    except TimeoutException:
        return False

def extract_line_value(line_text: str) -> Optional[float]:
    """Extrage valoarea numerică a liniei (ex: 'Over/Under +216.5' -> 216.5)."""
    match = re.search(r'(\d+\.?\d*)', line_text)
    if match:
        return float(match.group(1)) 
    return None

def get_match_slug(url: str) -> Optional[str]:
    """Extrage slug-ul meciului."""
    match = re.search(r'/[^/]+/[^/]+/([^/]+)/#', url)
    if match:
        return match.group(1)
    match_fallback = re.search(r'/[^/]+/[^/]+/([^/]+)/$', url)
    if match_fallback:
        return match_fallback.group(1)
    
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
    
    try:
        driver.execute_script("arguments[0].click();", element_to_click)
    except Exception as e:
        return f'Eroare: Cota Close nu a putut fi apăsată: {e}'

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
        return f'Eroare Click/Extracție Popup: {e}'


# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (INCLUSIV LOGICA CORECȚIEI PANDAS)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link: str, ah_link: str) -> Dict[str, Any]:
    
    global TARGET_BOOKMAKER_HREF_PARTIAL
    
    results: Dict[str, Any] = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver: Optional[webdriver.Chrome] = None 
    
    ou_lines: List[Dict[str, Any]] = []
    handicap_lines: List[Dict[str, Any]] = []

    # --- Inițializare driver ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080") 
    # ADAUGĂ USER-AGENT PENTRU A EVITA DETECTAREA BROWSERULUI
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului Headless. Detalii: {e}"
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = handicap_lines
        return dict(results)

    # Incepe scraping-ul
    try:
        driver.set_script_timeout(180) 
        
        COLLAPSED_ROW_XPATH_OU = '//div[@data-testid="over-under-collapsed-row"]'
        COLLAPSED_ROW_XPATH_AH = '//div[@data-testid="asian-handicap-collapsed-row"]'
        LINE_TEXT_REL_XPATH_SIMPLIFIED = './/div[@data-testid="over-under-collapsed-option-box"]/p[1]' 
        
        EXPANDED_ROW_STATIC_XPATH_OU = '//div[@data-testid="over-under-expanded-row"]'
        EXPANDED_ROW_STATIC_XPATH_AH = '//div[@data-testid="asian-handicap-expanded-row"]'
        
        HOME_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][1]//p[@class="odds-text"]' 
        AWAY_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][2]//p[@class="odds-text"]' 
        
        match_slug = get_match_slug(ou_link)
        if not match_slug:
            results['Error'] = "Eroare la extragerea slug-ului meciului din URL. Verifică formatul URL-ului."
            driver.quit()
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = handicap_lines
            return dict(results)

        # ----------------------------------------------------
        # ETAPA 1: Extrage liniile Over/Under (generare URL-uri)
        # ----------------------------------------------------
        if wait_for_collapsed_rows(driver, ou_link, "over-under-collapsed-row"):
            
            line_rows: List[WebElement] = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_OU)
            line_values: set[float] = set()
            
            for row in line_rows:
                try:
                    line_text_element = row.find_element(By.XPATH, LINE_TEXT_REL_XPATH_SIMPLIFIED)
                    value = extract_line_value(line_text_element.text.strip())
                    if value is not None:
                        line_values.add(value)
                except NoSuchElementException:
                    continue 
            
            # 2. Parcurge fiecare linie (URL) nou generată și extrage cotele
            for line_value in sorted(list(line_values)):
                new_url = BASE_URL_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
                
                driver.get(new_url)
                time.sleep(3) 

                try:
                    expanded_row = driver.find_element(By.XPATH, EXPANDED_ROW_STATIC_XPATH_OU)
                    
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
                            'Home_Over_Close': close_home,
                            'Home_Over_Open': open_home,
                            'Away_Under_Close': close_away,
                            'Away_Under_Open': open_away,
                            'Bookmaker': "Betano (Static URL)"
                        }
                        ou_lines.append(data)

                except NoSuchElementException:
                    continue
                except Exception:
                    continue
        else:
            results['O/U_Message'] = "Eroare: Nu s-au putut încărca rândurile O/U (Posibil anti-scraping)."


        # ----------------------------------------------------
        # ETAPA 2: Extrage liniile Handicap (Logica identică)
        # ----------------------------------------------------
        
        if wait_for_collapsed_rows(driver, ah_link, "asian-handicap-collapsed-row"):
            
            line_rows_ah: List[WebElement] = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_AH)
            line_values_ah: set[float] = set()
            
            for row in line_rows_ah:
                try:
                    line_text_element = row.find_element(By.XPATH, LINE_TEXT_REL_XPATH_SIMPLIFIED)
                    value = extract_line_value(line_text_element.text.strip())
                    if value is not None:
                        line_values_ah.add(value)
                except NoSuchElementException:
                    continue
            
            for line_value in sorted(list(line_values_ah)):
                new_url = BASE_URL_AH_TEMPLATE.format(match_slug=match_slug, line_value=line_value)
                
                driver.get(new_url)
                time.sleep(3) 
                
                try:
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
                    continue
                except Exception:
                    continue

        else:
            results['AH_Message'] = "Eroare: Nu s-au putut încărca rândurile AH (Posibil anti-scraping)."
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    results['Over_Under_Lines'] = ou_lines
    results['Handicap_Lines'] = handicap_lines
            
    return dict(results)
