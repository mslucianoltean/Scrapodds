# scraper_logic.py (VERSIUNEA ULTIMĂ - Bazat pe HTML-ul real)

import os
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 

def scrape_optimized_based_on_html(ou_link, ah_link):
    """Scraper ultra-rapid bazat pe structura HTML reală"""
    
    results = defaultdict(dict)
    driver = None
    
    # Configurație rapidă
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
        driver.set_page_load_timeout(15)
        
        # ----------------------------------------------------
        # OVER/UNDER - MAXIM 15 SECUNDE
        # ----------------------------------------------------
        print("=== SCRAPING OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(2)
        
        # 1. CLICK PE TABUL OVER/UNDER (folosind selectorul exact)
        ou_tab_xpath = "//li[@data-testid='navigation-active-tab']//div[text()='Over/Under']"
        try:
            ou_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, ou_tab_xpath))
            )
            driver.execute_script("arguments[0].click();", ou_tab)
            print("✓ Click pe tab Over/Under")
            time.sleep(2)
        except:
            print("✗ Tab Over/Under nu a putut fi apăsat")
        
        # 2. GĂSEȘTE TOATE LINIILE OVER/UNDER
        ou_lines = []
        
        # Selector pentru liniile Over/Under (bazat pe HTML-ul tău)
        line_selectors = [
            "//div[@data-testid='over-under-collapsed-option-box']",
            "//div[contains(@class, 'flex w-full items-center') and contains(., 'Over/Under')]"
        ]
        
        for selector in line_selectors:
            try:
                line_elements = driver.find_elements(By.XPATH, selector)
                print(f"Găsite {len(line_elements)} linii OU")
                
                for line_element in line_elements[:3]:  # Primele 3 linii
                    try:
                        # Extrage linia (ex: "+219.5")
                        line_text = line_element.text
                        line_value = None
                        if "Over/Under" in line_text:
                            # Extrage numărul după Over/Under
                            import re
                            match = re.search(r'Over/Under\s*([+-]?\d+\.?\d*)', line_text)
                            if match:
                                line_value = match.group(1)
                        
                        # Găsește rândul Betano după ce dăm click pe linie
                        driver.execute_script("arguments[0].click();", line_element)
                        time.sleep(1)
                        
                        # Caută Betano în rândurile care apar
                        betano_selectors = [
                            "//div[contains(@class, 'odds-cell') and contains(@class, 'bg-[#ffcf0d]')]",
                            "//div[@data-testid='odd-container']",
                            "//p[@data-testid='odd-container-default']"
                        ]
                        
                        home_odd = None
                        away_odd = None
                        
                        for bet_selector in betano_selectors:
                            try:
                                odds_elements = driver.find_elements(By.XPATH, bet_selector)
                                if len(odds_elements) >= 2:
                                    home_odd = odds_elements[0].text
                                    away_odd = odds_elements[1].text
                                    break
                            except:
                                continue
                        
                        if home_odd and away_odd:
                            # Extrage opening odds - dă click pe prima cotă
                            opening_home = get_opening_odds_optimized(driver, betano_selectors[0])
                            opening_away = get_opening_odds_optimized(driver, betano_selectors[1] if len(betano_selectors) > 1 else betano_selectors[0])
                            
                            ou_lines.append({
                                'Line': line_value or 'N/A',
                                'Home_Over_Close': home_odd,
                                'Home_Over_Open': opening_home,
                                'Away_Under_Close': away_odd, 
                                'Away_Under_Open': opening_away,
                                'Bookmaker': 'Betano'
                            })
                            print(f"✓ Linie OU găsită: {line_value} | {home_odd} | {away_odd}")
                            break
                            
                    except Exception as e:
                        print(f"Eroare linie OU: {e}")
                        continue
                
                if ou_lines:
                    break
                    
            except Exception as e:
                print(f"Eroare selector OU: {e}")
                continue
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ASIAN HANDICAP - MAXIM 15 SECUNDE
        # ----------------------------------------------------
        print("=== SCRAPING ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(2)
        
        # 1. CLICK PE TABUL ASIAN HANDICAP
        ah_tab_xpath = "//li[@data-testid='navigation-active-tab']//div[text()='Asian Handicap']"
        try:
            ah_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, ah_tab_xpath))
            )
            driver.execute_script("arguments[0].click();", ah_tab)
            print("✓ Click pe tab Asian Handicap")
            time.sleep(2)
        except:
            print("✗ Tab Asian Handicap nu a putut fi apăsat")
        
        # 2. GĂSEȘTE LINIILE ASIAN HANDICAP
        ah_lines = []
        
        # Selector pentru Asian Handicap (similar cu OU)
        ah_line_selectors = [
            "//div[contains(@class, 'flex w-full items-center') and contains(., 'Asian Handicap')]",
            "//div[@data-testid='over-under-collapsed-option-box']"
        ]
        
        for selector in ah_line_selectors:
            try:
                line_elements = driver.find_elements(By.XPATH, selector)
                print(f"Găsite {len(line_elements)} linii AH")
                
                for line_element in line_elements[:3]:
                    try:
                        # Extrage linia Asian Handicap
                        line_text = line_element.text
                        line_value = None
                        if "Asian Handicap" in line_text:
                            import re
                            match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                            if match:
                                line_value = match.group(1)
                        
                        driver.execute_script("arguments[0].click();", line_element)
                        time.sleep(1)
                        
                        # Cotele pentru Asian Handicap
                        home_odd = None
                        away_odd = None
                        
                        for bet_selector in betano_selectors:
                            try:
                                odds_elements = driver.find_elements(By.XPATH, bet_selector)
                                if len(odds_elements) >= 2:
                                    home_odd = odds_elements[0].text
                                    away_odd = odds_elements[1].text
                                    break
                            except:
                                continue
                        
                        if home_odd and away_odd:
                            opening_home = get_opening_odds_optimized(driver, betano_selectors[0])
                            opening_away = get_opening_odds_optimized(driver, betano_selectors[1] if len(betano_selectors) > 1 else betano_selectors[0])
                            
                            ah_lines.append({
                                'Line': line_value or 'N/A',
                                'Home_Over_Close': home_odd,
                                'Home_Over_Open': opening_home,
                                'Away_Under_Close': away_odd,
                                'Away_Under_Open': opening_away,
                                'Bookmaker': 'Betano'
                            })
                            print(f"✓ Linie AH găsită: {line_value} | {home_odd} | {away_odd}")
                            break
                            
                    except Exception as e:
                        print(f"Eroare linie AH: {e}")
                        continue
                
                if ah_lines:
                    break
                    
            except Exception as e:
                print(f"Eroare selector AH: {e}")
                continue
        
        results['Handicap_Lines'] = ah_lines
            
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return dict(results)

def get_opening_odds_optimized(driver, odds_selector):
    """Extrage opening odds rapid"""
    try:
        # Găsește elementul odds și dă click
        odds_element = driver.find_element(By.XPATH, odds_selector)
        driver.execute_script("arguments[0].click();", odds_element)
        time.sleep(1)
        
        # Caută opening odds în popup (bazat pe HTML-ul tău)
        opening_selectors = [
            "//div[contains(text(), 'Opening odds:')]/following-sibling::div//div[@class='font-bold']",
            "//div[contains(., 'Opening odds')]//div[contains(@class, 'font-bold')]",
            "//div[contains(., 'Opening odds')]"
        ]
        
        for selector in opening_selectors:
            try:
                opening_element = driver.find_element(By.XPATH, selector)
                opening_text = opening_element.text
                # Extrage doar numărul (ex: "5.00")
                import re
                match = re.search(r'(\d+\.?\d*)', opening_text)
                if match:
                    return match.group(1)
            except:
                continue
        
        return 'N/A'
        
    except:
        return 'N/A'

# Folosește această funcție în Streamlit
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_optimized_based_on_html(ou_link, ah_link)
