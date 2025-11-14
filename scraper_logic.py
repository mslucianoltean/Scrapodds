# scraper_logic.py (VERSIUNEA FINALĂ CU CĂUTARE GENERALĂ RÂNDURI)

# ... (restul importurilor și configurației rămân neschimbate) ...

# ------------------------------------------------------------------------------
# 🛠️ FUNCȚII AJUTĂTOARE SELENIUM 
# ------------------------------------------------------------------------------
# ... (Funcțiile find_element, ffi, ffi2, get_opening_odd, fffi rămân neschimbate) ...

# AM MODIFICAT ACEASTĂ FUNCȚIE PENTRU A FOLOSI UN NUME DINTR-O POZIȚIE MAI SIMPLĂ (div[1])
def get_bookmaker_name_from_div(driver, row_xpath):
    """Extrage numele bookmakerului dintr-un rând bazat pe DIV, căutând în prima div."""
    # În loc să căutăm după clasă, căutăm simplu primul DIV din rând
    xpath = f'{row_xpath}/div[1]' 
    element = find_element(driver, By.XPATH, xpath)
    return element.text.strip() if element else None

# ------------------------------------------------------------------------------
# 🚀 FUNCȚIA PRINCIPALĂ DE SCRAPING (ANCORĂ PE CONTAINER COTE)
# ------------------------------------------------------------------------------

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    global TARGET_BOOKMAKER 
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver = None 

    # --- Inițializare driver ---
    # ... (blocul de inițializare rămâne neschimbat) ...
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
        wait = WebDriverWait(driver, 20)
        
        # ANCORE
        general_anchor_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[1]'
        base_rows_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]'

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        driver.get(ou_link)
        
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

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, general_anchor_xpath)))
        except:
            results['Error'] = "Eroare la încărcarea paginii Over/Under (Ancora generală nu a fost găsită)."
            driver.quit()
            return dict(results)

        wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        
        ou_lines = []
        time.sleep(3) 
        
        # Extrage liniile OU 
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            # Verificăm dacă rândul există, altfel ieșim din buclă
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break
            
            # NOU: Folosim funcția simplificată get_bookmaker_name_from_div
            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                
                home_odd_xpath = f'{row_container_xpath}/div[1]' 
                away_odd_xpath = f'{row_container_xpath}/div[2]' 
                
                # ... (restul logicii de extragere a cotelor rămâne neschimbată) ...
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away:
                    line_raw_text = close_home 
                    line_match = re.search(r'[+-]?\d+\.?\d*', line_raw_text)
                    line = line_match.group(0) if line_match else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': 'DEZACTIVAT (instabil)',
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': 'DEZACTIVAT (instabil)',
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        ou_lines.append(data)
        
        results['Over_Under_Lines'] = ou_lines

        # ----------------------------------------------------
        # ETAPA 2: Extrage cotele Handicap
        # ----------------------------------------------------
        driver.get(ah_link)
        
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

        wait.until(EC.visibility_of_element_located((By.XPATH, general_anchor_xpath)))
        wait.until(EC.visibility_of_element_located((By.XPATH, base_rows_xpath)))
        
        handicap_lines = []
        time.sleep(3) 

        # Extrage liniile AH 
        for j in range(1, 101):
            row_container_xpath = f'{base_rows_xpath}/div[{j}]'
            
            row_element = find_element(driver, By.XPATH, row_container_xpath)
            if not row_element and j > 5: break

            bm_name = get_bookmaker_name_from_div(driver, row_container_xpath)
            
            if bm_name and TARGET_BOOKMAKER in bm_name:
                home_odd_xpath = f'{row_container_xpath}/div[1]' 
                away_odd_xpath = f'{row_container_xpath}/div[2]' 
                
                close_home = fffi(driver, home_odd_xpath)
                close_away = fffi(driver, away_odd_xpath)
                
                if close_home and close_away:
                    line_raw_text = close_home 
                    line_match = re.search(r'[+-]?\d+\.?\d*', line_raw_text)
                    line = line_match.group(0) if line_match else 'N/A'
                    
                    data = {
                        'Line': line,
                        'Home_Over_Close': close_home,
                        'Home_Over_Open': 'DEZACTIVAT (instabil)',
                        'Away_Under_Close': close_away,
                        'Away_Under_Open': 'DEZACTIVAT (instabil)',
                        'Bookmaker': bm_name
                    }
                    if data['Line'] != 'N/A':
                        handicap_lines.append(data)

        results['Handicap_Lines'] = handicap_lines
            
    except Exception as e:
        results['Runtime_Error'] = f"A apărut o eroare neașteptată în timpul scraping-ului: {e}"
    
    finally:
        if driver:
            driver.quit() 
            
    return dict(results)
