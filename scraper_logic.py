# scraper_logic.py (VERSIUNEA 20.0 - Optimizat pentru Pagini Dinamice)

import os
import time
import random
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
# ⚙️ CONFIGURARE AVANSATĂ
# ------------------------------------------------------------------------------
TARGET_BOOKMAKER_HREF_PARTIAL = "betano"
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE ÎMBUNĂTĂȚITE
# ------------------------------------------------------------------------------

def human_like_delay(min_seconds=0.5, max_seconds=2):
    """Așteaptă un timp aleatoriu pentru a imita comportamentul uman."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def scroll_to_element(driver, element):
    """Face scroll către element pentru a-l aduce în viewport."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        human_like_delay(0.3, 0.7)
    except:
        pass

def wait_for_page_load(driver, timeout=30):
    """Așteaptă până când pagina este complet încărcată."""
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

def find_and_click_tab(driver, tab_name, max_retries=3):
    """Găsește și dă click pe un tab după nume cu retry-uri."""
    selectors = [
        f"//div[contains(text(), '{tab_name}')]",
        f"//button[contains(text(), '{tab_name}')]",
        f"//a[contains(text(), '{tab_name}')]",
        f"//*[contains(@class, 'tab') and contains(text(), '{tab_name}')]",
        f"//*[contains(text(), '{tab_name}')]",
        f"//*[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{tab_name.lower()}']"
    ]
    
    for attempt in range(max_retries):
        for selector in selectors:
            try:
                print(f"Încerc selector: {selector} (încercarea {attempt + 1})")
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                
                # Scroll și highlight
                scroll_to_element(driver, element)
                driver.execute_script("arguments[0].style.border='2px solid red';", element)
                
                # Click cu JavaScript
                driver.execute_script("arguments[0].click();", element)
                
                human_like_delay(1, 2)
                
                # Verifică dacă click-ul a avut efect
                driver.execute_script("arguments[0].style.border='';", element)
                return True
                
            except Exception as e:
                print(f"Selector {selector} a eșuat: {e}")
                continue
        
        # Dacă niciun selector nu funcționează, încercă refresh
        if attempt < max_retries - 1:
            driver.refresh()
            human_like_delay(2, 4)
            wait_for_page_load(driver)
    
    return False

def expand_all_lines(driver):
    """Încearcă să expandeze toate liniile de cote."""
    expand_buttons = [
        "//div[contains(@class, 'table-main__row--details-line-wrapper')]",
        "//div[contains(@class, 'table-main__row--more')]",
        "//div[contains(@class, 'expand')]",
        "//div[contains(@class, 'show-more')]",
        "//button[contains(text(), 'More')]"
    ]
    
    for selector in expand_buttons:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements[:3]:  # Încearcă doar primele 3
                try:
                    scroll_to_element(driver, element)
                    driver.execute_script("arguments[0].click();", element)
                    human_like_delay(0.5, 1)
                except:
                    pass
            break
        except:
            continue

def find_betano_row_advanced(driver, line_row_element):
    """Găsește rândul Betano folosind multiple strategii."""
    strategies = [
        # Strategia 1: Caută direct după href
        f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/ancestor::div[contains(@class, "table-main__row--details-line")]',
        
        # Strategia 2: Caută după text Betano
        './/p[contains(text(), "Betano")]/ancestor::div[contains(@class, "table-main__row--details-line")]',
        './/span[contains(text(), "Betano")]/ancestor::div[contains(@class, "table-main__row--details-line")]',
        
        # Strategia 3: Caută în toate rândurile de detalii
        './/div[contains(@class, "table-main__row--details-line")]',
        
        # Strategia 4: Caută orice element care conține Betano
        './/*[contains(text(), "Betano")]/ancestor::div[contains(@class, "row")]'
    ]
    
    for strategy in strategies:
        try:
            element = line_row_element.find_element(By.XPATH, strategy)
            print(f"Găsit Betano cu strategia: {strategy}")
            return element
        except NoSuchElementException:
            continue
    
    return None

def get_opening_odd_from_click_improved(driver, element_to_click_xpath):
    """Versiune îmbunătățită pentru extragerea cotelor de deschidere."""
    
    try:
        # Găsește elementul pentru click
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, element_to_click_xpath))
        )
        
        # Scroll și highlight
        scroll_to_element(driver, element)
        driver.execute_script("arguments[0].style.border='2px solid blue';", element)
        
        # Click cu JavaScript
        driver.execute_script("arguments[0].click();", element)
        human_like_delay(1, 1.5)
        
        # Așteaptă popup-ul cu multiple selectori
        popup_selectors = [
            '//*[@id="tooltip_v"]//div[2]/p[@class="odds-text"]',
            '//*[contains(@class, "tooltip")]//p[contains(@class, "odds-text")]',
            '//*[contains(@class, "popup")]//p[contains(@class, "odds")]',
            '//*[contains(@class, "modal")]//p[contains(text(), ".")]'  # pentru numere cu zecimale
        ]
        
        opening_odd_text = None
        for selector in popup_selectors:
            try:
                opening_odd_element = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.XPATH, selector))
                )
                opening_odd_text = opening_odd_element.text.strip()
                print(f"Găsit opening odd: {opening_odd_text}")
                break
            except TimeoutException:
                continue
        
        # Închide popup-ul făcând click în altă parte
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            body.click()
        except:
            pass
        
        human_like_delay(0.5, 1)
        
        return opening_odd_text if opening_odd_text else 'N/A'
        
    except Exception as e:
        print(f"Eroare la get_opening_odd: {e}")
        return f'Eroare: {str(e)}'

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING ÎMBUNĂTĂȚITĂ
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    global TARGET_BOOKMAKER_HREF_PARTIAL 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping optimizat pentru pagini dinamice'
    driver = None 
    
    # --- Inițializare driver avansată ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Optimizări pentru pagini dinamice
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
    })
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    except Exception as e:
        results['Error'] = f"Eroare la inițializarea driverului: {e}"
        return dict(results)

    try:
        wait = WebDriverWait(driver, 30)
        
        # ----------------------------------------------------
        # ETAPA 1: Over/Under cu logica îmbunătățită
        # ----------------------------------------------------
        print("=== ÎNCEPE SCRAPING OVER/UNDER ===")
        driver.get(ou_link)
        
        # Așteaptă încărcarea completă a paginii
        wait_for_page_load(driver)
        human_like_delay(2, 3)
        
        # Facem scroll pentru a încărca content-ul lazy
        driver.execute_script("window.scrollTo(0, 300);")
        human_like_delay(1, 2)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Clic pe tabul Over/Under
        if not find_and_click_tab(driver, "Over/Under"):
            results['OU_Error'] = "Nu s-a putut găsi sau apăsa tabul Over/Under"
            # Continuăm anyway, poate tab-ul este deja activ
            
        human_like_delay(2, 3)
        
        # Încearcă să expandeze liniile
        expand_all_lines(driver)
        human_like_delay(1, 2)
        
        # Așteaptă liniile să fie vizibile
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "table-main__row--details-line-wrapper")]')))
        except:
            print("Nu s-au găsit linii imediat, continuăm...")
        
        # Extrage liniile OU
        ou_lines = []
        all_line_rows = driver.find_elements(By.XPATH, '//div[contains(@class, "table-main__row--details-line-wrapper")]')
        print(f"Găsite {len(all_line_rows)} linii OU")
        
        for i, line_row_element in enumerate(all_line_rows[:5]):  # Limită la primele 5 linii
            try:
                print(f"Procesez linia OU {i+1}")
                
                # Expandare linie
                scroll_to_element(driver, line_row_element)
                driver.execute_script("arguments[0].click();", line_row_element)
                human_like_delay(1, 2)
                
                # Găsește rândul Betano
                betano_row_element = find_betano_row_advanced(driver, line_row_element)
                
                if not betano_row_element:
                    print(f"Nu s-a găsit Betano pe linia {i+1}")
                    continue
                
                # Extrage linia
                line_raw_text = ffi(betano_row_element, By.XPATH, './/span[contains(@class, "table-main__detail-line-more")]')
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                print(f"Linia găsită: {line}")
                
                # Extrage cotele
                home_odd = ffi(betano_row_element, By.XPATH, './/div[contains(@class, "odds")]')
                away_odd = ffi(betano_row_element, By.XPATH, './/div[contains(@class, "odds")][2]')
                
                if home_odd and away_odd:
                    data = {
                        'Line': line,
                        'Home_Over_Close': home_odd,
                        'Home_Over_Open': 'N/A',  # Vom completa mai târziu
                        'Away_Under_Close': away_odd,
                        'Away_Under_Open': 'N/A',  # Vom completa mai târziu
                        'Bookmaker': 'Betano'
                    }
                    ou_lines.append(data)
                    print(f"Adăugat linie OU: {data}")
                    break  # Prima linie validă este suficientă
                    
            except Exception as e:
                print(f"Eroare la procesarea liniei OU {i+1}: {e}")
            finally:
                # Colapsează linia
                try:
                    driver.execute_script("arguments[0].click();", line_row_element)
                except:
                    pass
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Asian Handicap cu aceeași logică
        # ----------------------------------------------------
        print("=== ÎNCEPE SCRAPING ASIAN HANDICAP ===")
        driver.get(ah_link)
        
        # Așteaptă încărcarea completă a paginii
        wait_for_page_load(driver)
        human_like_delay(2, 3)
        
        # Scroll pentru a încărca content-ul
        driver.execute_script("window.scrollTo(0, 300);")
        human_like_delay(1, 2)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Clic pe tabul Asian Handicap
        if not find_and_click_tab(driver, "Asian Handicap"):
            results['AH_Error'] = "Nu s-a putut găsi sau apăsa tabul Asian Handicap"
            
        human_like_delay(2, 3)
        
        # Expandare linii
        expand_all_lines(driver)
        human_like_delay(1, 2)
        
        # Extrage liniile AH
        handicap_lines = []
        all_line_rows = driver.find_elements(By.XPATH, '//div[contains(@class, "table-main__row--details-line-wrapper")]')
        print(f"Găsite {len(all_line_rows)} linii AH")
        
        for i, line_row_element in enumerate(all_line_rows[:5]):
            try:
                print(f"Procesez linia AH {i+1}")
                
                scroll_to_element(driver, line_row_element)
                driver.execute_script("arguments[0].click();", line_row_element)
                human_like_delay(1, 2)
                
                betano_row_element = find_betano_row_advanced(driver, line_row_element)
                
                if not betano_row_element:
                    print(f"Nu s-a găsit Betano pe linia AH {i+1}")
                    continue
                
                line_raw_text = ffi(betano_row_element, By.XPATH, './/span[contains(@class, "table-main__detail-line-more")]')
                line = line_raw_text.strip() if line_raw_text else 'N/A'
                
                print(f"Linia AH găsită: {line}")
                
                home_odd = ffi(betano_row_element, By.XPATH, './/div[contains(@class, "odds")]')
                away_odd = ffi(betano_row_element, By.XPATH, './/div[contains(@class, "odds")][2]')
                
                if home_odd and away_odd:
                    data = {
                        'Line': line,
                        'Home_Over_Close': home_odd,
                        'Home_Over_Open': 'N/A',
                        'Away_Under_Close': away_odd,
                        'Away_Under_Open': 'N/A',
                        'Bookmaker': 'Betano'
                    }
                    handicap_lines.append(data)
                    print(f"Adăugat linie AH: {data}")
                    break
                    
            except Exception as e:
                print(f"Eroare la procesarea liniei AH {i+1}: {e}")
            finally:
                try:
                    driver.execute_script("arguments[0].click();", line_row_element)
                except:
                    pass
        
        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"Eroare neașteptată: {e}"
        import traceback
        results['Traceback'] = traceback.format_exc()
    
    finally:
        if driver:
            driver.quit()
            
    print("=== SCRAPING COMPLET ===")
    return dict(results)

# Păstrăm funcțiile originale pentru compatibilitate
def ffi(element_or_driver, by_method, locator):
    try:
        element = element_or_driver.find_element(by_method, locator)
        return element.text.strip()
    except NoSuchElementException:
        return None

def ffi2(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", element)
        return True
    except:
        return False
