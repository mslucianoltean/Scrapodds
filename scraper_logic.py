# scraper_logic.py (VERSIUNEA 37.0 - XPath simplificat bazat pe 'following::')

# ... (Importuri și funcții ajutătoare rămân neschimbate) ...

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    
    global TARGET_BOOKMAKER_HREF_PARTIAL
    
    results = defaultdict(dict)
    results['Match'] = 'Scraping activat'
    driver = None 
    
    # --- Inițializare driver --- (Rămâne neschimbată)
    # ...
    # ------------------------------------------------------------------------------

    # Incepe scraping-ul
    try:
        driver.set_script_timeout(180) 
        wait = WebDriverWait(driver, 30)
        
        # Punctele de referință
        LINE_ROWS_XPATH = '//div[contains(@data-testid, "collapsed-row")]' 
        LINE_CLICK_REL_PATH = './/p[contains(@class, "max-sm:!hidden")]' # Elementul pe care dăm clic

        # Căi interne (UPDATE 37.0 - Simplificare Brutală)
        
        # 1. Găsim rândul expandat
        EXPANDED_ROW_XPATH = './following-sibling::div[1]//div[@data-testid="over-under-expanded-row"]'
        
        # 2. Căutăm cotele Betano (utilizând EXPANDED_ROW ca bază)
        # Atenție: Aici folosim '//a' pentru a căuta link-ul Betano oriunde în subarborele rândului expandat,
        # și apoi navigăm la cotele care urmează link-ul, indiferent de nivelul lor.
        
        HOME_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][1]//p[@class="odds-text"]' 
        AWAY_ODD_REL_PATH = f'.//a[contains(@href, "{TARGET_BOOKMAKER_HREF_PARTIAL}")]/following::div[@data-testid="odd-container"][2]//p[@class="odds-text"]' 
        
        LINE_REL_PATH = LINE_CLICK_REL_PATH 

        # ----------------------------------------------------
        # ETAPA 1: Extrage cotele Over/Under
        # ----------------------------------------------------
        # ... (Logica de extragere rămâne neschimbată) ...
        # ... (Logica de extracție în interiorul try/except) ...
        
        driver.get(ou_link)
        
        try:
            # ... (Logica de așteptare) ...
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
                driver.execute_script("arguments[0].click();", element_to_click)
                time.sleep(1.5) 
                
            except Exception as e:
                continue 

            try:
                # Găsim rândul expandat care conține bookmakerii
                expanded_row = line_row_element.find_element(By.XPATH, EXPANDED_ROW_XPATH)
                
                # 2. Încercăm să extragem datele din rândul de detaliu deschis
                line_raw_text = element_to_click.text.strip()
                line = line_raw_text if line_raw_text else 'N/A'
                
                # Căutarea cotelor în interiorul expanded_row folosind noile căi:
                home_odd_element = expanded_row.find_element(By.XPATH, HOME_ODD_REL_PATH)
                close_home = home_odd_element.text.strip()
                
                away_odd_element = expanded_row.find_element(By.XPATH, AWAY_ODD_REL_PATH)
                close_away = away_odd_element.text.strip()
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    home_odd_xpath_full = driver.execute_script("""...""", home_odd_element)
                    away_odd_xpath_full = driver.execute_script("""...""", away_odd_element)
                    
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath_full)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath_full)
                    
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
                        break 
                        
            except NoSuchElementException as e:
                # Eșecul de extracție se întâmplă aici
                pass 
            
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
        
        # ... (Logica AH identică) ...
        
        driver.get(ah_link)
        
        try:
            # ... (Logica de așteptare) ...
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
                
                if close_home and close_away and close_home != 'N/A' and close_away != 'N/A':
                    
                    home_odd_xpath_full = driver.execute_script("""...""", home_odd_element)
                    away_odd_xpath_full = driver.execute_script("""...""", away_odd_element)
                    
                    open_home = get_opening_odd_from_click(driver, home_odd_xpath_full)
                    time.sleep(0.5)
                    open_away = get_opening_odd_from_click(driver, away_odd_xpath_full)

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
