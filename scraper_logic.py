# scraper_logic.py (VERSIUNEA 45.0 - DEBUG Linii)

import os
import time
import re 
from collections import defaultdict 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from typing import Optional, Dict, Any

# ------------------------------------------------------------------------------
# ⚙️ CONFIGURARE
# ------------------------------------------------------------------------------
# Am simplificat la template-ul de bază, deoarece nu generăm URL-uri complete
BASE_URL_TEMPLATE = "https://www.oddsportal.com/basketball/usa/nba/{match_slug}/#over-under;1;{line_value:.2f};0"
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE
# ------------------------------------------------------------------------------

def get_match_slug(url: str) -> Optional[str]:
    """Extrage slug-ul meciului, gestionând și URL-urile incomplete."""
    match = re.search(r'/[^/]+/[^/]+/([^/]+)/#', url)
    if match:
        return match.group(1)
    match_fallback = re.search(r'/[^/]+/[^/]+/([^/]+)/$', url)
    if match_fallback:
        return match_fallback.group(1)
    return None

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


# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE DEBUG
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link: str, ah_link: str) -> Dict[str, Any]:
    
    results: Dict[str, Any] = defaultdict(dict)
    driver: Optional[webdriver.Chrome] = None 
    
    # --- Extragerea slug-ului ---
    match_slug = get_match_slug(ou_link)
    if not match_slug:
        results['Error'] = "Eroare la extragerea slug-ului din URL."
        return dict(results)
    
    results['Match_Slug'] = match_slug

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
        results['Error'] = f"Eroare la inițializarea driverului Headless: {e}"
        return dict(results)

    # Incepe debug-ul pe Over/Under
    try:
        driver.set_script_timeout(180) 
        
        COLLAPSED_ROW_XPATH_OU = '//div[@data-testid="over-under-collapsed-row"]'
        COLLAPSED_ROW_XPATH_AH = '//div[@data-testid="asian-handicap-collapsed-row"]'
        
        # ----------------------------------------------------
        # TEST 1: Așteptare și Navigare (O/U)
        # ----------------------------------------------------
        if wait_for_collapsed_rows(driver, ou_link, "over-under-collapsed-row"):
            
            # TEST 2: Numărarea rândurilor colapsate
            line_rows_ou = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_OU)
            results['Found_OU_Rows'] = len(line_rows_ou)
            
            # ----------------------------------------------------
            # TEST 3: Numărarea rândurilor colapsate (AH)
            # ----------------------------------------------------
            if wait_for_collapsed_rows(driver, ah_link, "asian-handicap-collapsed-row"):
                line_rows_ah = driver.find_elements(By.XPATH, COLLAPSED_ROW_XPATH_AH)
                results['Found_AH_Rows'] = len(line_rows_ah)
            else:
                 results['Found_AH_Rows'] = "Eroare la așteptarea rândurilor AH."
            
            
            if len(line_rows_ou) == 0:
                results['Message'] = "Gata! Am extras slug-ul, dar nu am găsit NICIUN rând de linii O/U. Problema e la XPath sau încărcare."
            else:
                results['Message'] = "SUCCES! Am găsit cel puțin un rând de linii. Acum putem începe scraping-ul cotelor."
                # Dacă am găsit rânduri, returnăm primele 3 texte pentru a le inspecta.
                top_texts = []
                for row in line_rows_ou[:3]:
                    try:
                        # Folosim un XPath mai general pentru a obține text
                        text = row.text.replace('\n', ' | ')
                        top_texts.append(text)
                    except:
                        top_texts.append("Eroare la extragerea textului rândului.")
                results['Top_3_OU_Row_Text'] = top_texts


        else:
            results['Error'] = "Eroare: Rândurile O/U NU au apărut după 20 de secunde (Timeout)."
            results['Found_OU_Rows'] = 0


    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul debug-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
