from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re
import sys
import subprocess
import os
from typing import Optional, List, Dict

def install_playwright():
    """Instalează Playwright dacă nu este disponibil"""
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright este instalat")
        
        # Testează dacă chromium funcționează
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, timeout=15000)
                browser.close()
            print("✓ Chromium funcționează corect")
        except Exception as e:
            print(f"⚠️ Problema cu Chromium: {e}")
            print("📥 Se reinstalează browserele...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            
    except ImportError:
        print("❌ Playwright nu este instalat. Se instalează...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

# Verifică și instalează la început
install_playwright()

def scrape_betano_odds(match_url: str, headless: bool = True, progress_callback=None) -> Optional[List[Dict]]:
    """
    Scrape-ează cotele Betano Over/Under de pe OddsPortal
    """
    results = []
    
    def log(msg):
        if progress_callback:
            progress_callback(msg)
        print(f"LOG: {msg}")  # Pentru debugging în console
    
    try:
        with sync_playwright() as p:
            log("🌐 Se lansează browser-ul...")
            
            # Opțiuni de launch optimizate pentru server
            launch_options = {
                'headless': headless,
                'timeout': 30000
            }
            
            # Argumente pentru medii server
            if os.environ.get('STREAMLIT_SHARED_MODE') or not headless:
                launch_options['args'] = [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            
            browser = p.chromium.launch(**launch_options)
            
            # Context cu setări realiste
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True,
                bypass_csp=True
            )
            
            page = context.new_page()
            
            # Navigare la pagină
            log("🌐 Se încarcă pagina OddsPortal...")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            
            # Așteaptă încărcarea elementelor principale
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(3)
            
            # Verifică dacă suntem pe pagina corectă
            page_title = page.title()
            log(f"📄 Pagina încărcată: {page_title}")
            
            # DEBUG: Salvează screenshot pentru analiză
            try:
                page.screenshot(path="/tmp/debug_initial.png", full_page=True)
                log("📸 Screenshot salvat: /tmp/debug_initial.png")
            except Exception as e:
                log(f"⚠️ Nu s-a putut salva screenshot: {e}")
            
            # Verifică dacă URL-ul conține deja over-under
            if '#over-under' not in page.url:
                log("🔄 Se navighează la tab-ul Over/Under...")
                over_under_url = add_over_under_hash(page.url)
                page.goto(over_under_url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(3)
            
            # Așteaptă încărcarea tabelelor de cote
            log("⏳ Se așteaptă încărcarea tabelelor...")
            time.sleep(5)
            
            # DEBUG: Screenshot după navigare
            try:
                page.screenshot(path="/tmp/debug_after_nav.png", full_page=True)
                log("📸 Screenshot după navigare salvat")
            except:
                pass
            
            # Găsește rândul Betano folosind metode multiple
            log("🔍 Se caută bookmaker-ul Betano...")
            betano_row = find_betano_row_advanced(page)
            
            if not betano_row:
                log("❌ Betano nu a fost găsit în listă")
                
                # Încearcă metode alternative
                log("🔄 Se încearcă metode alternative...")
                betano_row = find_betano_alternative_methods(page)
                
                if not betano_row:
                    log("❌ Betano nu este disponibil pentru acest meci")
                    
                    # Listă bookmakers disponibili pentru debugging
                    try:
                        bookmakers = page.locator('[class*="bookmaker"], [class*="provider"], tr, div[class*="row"]')
                        count = bookmakers.count()
                        log(f"ℹ️ Număr total de bookmakers găsiți: {count}")
                        
                        # Extrage primele 5 bookmakers pentru debugging
                        for i in range(min(5, count)):
                            try:
                                text = bookmakers.nth(i).inner_text()[:100]  # Primele 100 de caractere
                                log(f"Bookmaker {i+1}: {text}")
                            except:
                                pass
                    except Exception as e:
                        log(f"⚠️ Eroare la listarea bookmakers: {e}")
                    
                    browser.close()
                    return None
            
            log("✅ Betano găsit! Se extrag cotele...")
            
            # DEBUG: Screenshot cu Betano evidențiat
            try:
                betano_row.highlight()
                page.screenshot(path="/tmp/debug_betano.png", full_page=True)
                log("📸 Screenshot cu Betano salvat")
            except:
                pass
            
            # Extrage cotele closing
            log("📊 Se extrag cotele closing...")
            closing_odds = extract_closing_odds_advanced(betano_row, page)
            
            if closing_odds:
                results.append(closing_odds)
                log(f"✅ Closing: Over {closing_odds['over']} | Under {closing_odds['under']}")
            else:
                log("❌ Nu s-au putut extrage cotele closing")
            
            # Încearcă să extragă opening odds
            log("🔄 Se încearcă extragerea opening odds...")
            opening_odds = extract_opening_odds_advanced(page, betano_row)
            
            if opening_odds:
                results.append(opening_odds)
                log(f"✅ Opening: Over {opening_odds['over']} | Under {opening_odds['under']}")
            else:
                log("ℹ️ Opening odds nu sunt disponibile")
            
            browser.close()
            
            if results:
                log("🎉 Scraping finalizat cu succes!")
                return results
            else:
                log("❌ Nu s-au putut extrage datele")
                return None
            
    except Exception as e:
        log(f"❌ Eroare critică: {str(e)}")
        import traceback
        log(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None

def find_betano_row_advanced(page):
    """Găsește rândul Betano folosind metode multiple"""
    
    # Metoda 1: Caută după textul Betano în întreaga pagină
    try:
        betano_elements = page.locator('text=/betano/i')
        count = betano_elements.count()
        log(f"🔍 Elemente Betano găsite: {count}")
        
        for i in range(count):
            try:
                element = betano_elements.nth(i)
                if element.is_visible():
                    # Navighează în sus pentru a găsi containerul părinte
                    row = element.locator('xpath=./ancestor::tr[1] | ./ancestor::div[contains(@class, "row")][1] | ./ancestor::div[contains(@class, "eventRow")][1] | ./ancestor::div[@data-testid][1] | ./ancestor::*[@id][1]').first
                    if row.is_visible():
                        log("✅ Betano găsit prin metoda text")
                        return row
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare metoda text: {e}")
    
    # Metoda 2: Caută în tabele specifice OddsPortal
    try:
        table_selectors = [
            '[class*="table"]',
            '[data-testid*="table"]',
            '.eventRow',
            '.flex-row',
            '.table-main',
            '#table-main',
            '.odds-table'
        ]
        
        for selector in table_selectors:
            try:
                rows = page.locator(f'{selector} >> tr, {selector} >> div[class*="row"]')
                row_count = rows.count()
                log(f"🔍 Rânduri găsite cu selector {selector}: {row_count}")
                
                for i in range(row_count):
                    try:
                        row = rows.nth(i)
                        if row.is_visible():
                            text = row.inner_text().lower()
                            if 'betano' in text:
                                log(f"✅ Betano găsit în tabel cu selector: {selector}")
                                return row
                    except:
                        continue
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare metoda tabele: {e}")
    
    # Metoda 3: XPath direct
    try:
        xpath_queries = [
            '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]/ancestor::tr[1]',
            '//tr[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]',
            '//div[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]/ancestor::div[contains(@class, "row")][1]'
        ]
        
        for xpath in xpath_queries:
            try:
                row = page.locator(f"xpath={xpath}").first
                if row.is_visible():
                    log(f"✅ Betano găsit cu XPath: {xpath[:50]}...")
                    return row
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare metoda XPath: {e}")
    
    return None

def find_betano_alternative_methods(page):
    """Metode alternative pentru a găsi Betano"""
    
    # Metoda: Extrage toate rândurile și caută manual
    try:
        all_rows = page.locator('tr, div[class*="row"], div[class*="event"]')
        count = all_rows.count()
        log(f"🔍 Total rânduri pagină: {count}")
        
        for i in range(min(count, 50)):  # Verifică doar primele 50
            try:
                row = all_rows.nth(i)
                if row.is_visible():
                    text = row.inner_text().lower()
                    if 'betano' in text:
                        log(f"✅ Betano găsit prin scanare rânduri (index {i})")
                        return row
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare scanare rânduri: {e}")
    
    return None

def extract_closing_odds_advanced(betano_row, page):
    """Extrage cotele closing cu metode robuste"""
    
    try:
        # Metoda 1: Caută elemente cu cote în rândul Betano
        odds_elements = betano_row.locator('*')
        elements_count = odds_elements.count()
        log(f"🔍 Elemente în rândul Betano: {elements_count}")
        
        found_odds = []
        
        for i in range(elements_count):
            try:
                element = odds_elements.nth(i)
                if element.is_visible():
                    text = element.inner_text().strip()
                    
                    # Verifică dacă textul este o cotă validă
                    if re.match(r'^\d+\.\d{2}$', text):
                        odds_value = float(text)
                        if 1.0 <= odds_value <= 50.0:  # Filtru pentru cote realiste
                            found_odds.append(odds_value)
                            log(f"📊 Cotă găsită: {odds_value}")
                            
                            if len(found_odds) >= 2:
                                break
            except:
                continue
        
        if len(found_odds) >= 2:
            return {
                'type': 'Closing',
                'over': found_odds[0],
                'under': found_odds[1]
            }
        
        # Metoda 2: Extrage toate numerele din textul rândului
        row_text = betano_row.inner_text()
        log(f"📝 Text rând Betano: {row_text[:200]}...")
        
        all_numbers = re.findall(r'\d+\.\d{2}', row_text)
        log(f"🔢 Numere găsite în text: {all_numbers}")
        
        # Filtrează numerele pentru a găsi cote valide
        valid_odds = []
        for num in all_numbers:
            odds_val = float(num)
            if 1.0 <= odds_val <= 50.0:  # Cote normale pentru Over/Under
                valid_odds.append(odds_val)
        
        if len(valid_odds) >= 2:
            return {
                'type': 'Closing',
                'over': valid_odds[0],
                'under': valid_odds[1]
            }
        
        # Metoda 3: Caută în elemente specifice de cote
        odds_selectors = [
            '[class*="odds"]',
            '[class*="price"]',
            '[class*="bet"]',
            '.odds',
            '.price',
            '.bet'
        ]
        
        for selector in odds_selectors:
            try:
                odds_cells = betano_row.locator(selector)
                count = odds_cells.count()
                
                for i in range(count):
                    try:
                        cell = odds_cells.nth(i)
                        if cell.is_visible():
                            text = cell.inner_text().strip()
                            numbers = re.findall(r'\d+\.\d{2}', text)
                            if numbers:
                                odds_val = float(numbers[0])
                                if 1.0 <= odds_val <= 50.0:
                                    found_odds.append(odds_val)
                                    if len(found_odds) >= 2:
                                        return {
                                            'type': 'Closing',
                                            'over': found_odds[0],
                                            'under': found_odds[1]
                                        }
                    except:
                        continue
            except:
                continue
        
    except Exception as e:
        log(f"❌ Eroare extragere closing odds: {e}")
    
    return None

def extract_opening_odds_advanced(page, betano_row):
    """Extrage opening odds cu metode avansate"""
    
    try:
        # Găsește elemente clickable în rândul Betano
        clickable_selectors = [
            'a',
            'button',
            '[href]',
            '[onclick]',
            '[class*="click"]',
            '[class*="odds"]',
            '[class*="price"]'
        ]
        
        for selector in clickable_selectors:
            try:
                clickable_elements = betano_row.locator(selector)
                count = clickable_elements.count()
                
                for i in range(count):
                    try:
                        element = clickable_elements.nth(i)
                        if element.is_visible() and element.is_enabled():
                            
                            log(f"🖱️ Click pe element {i+1}/{count}")
                            element.click()
                            time.sleep(2)
                            
                            # Caută popup-ul
                            popup = find_popup_advanced(page)
                            if popup:
                                opening_odds = extract_odds_from_popup_advanced(popup)
                                if opening_odds:
                                    # Închide popup-ul
                                    page.keyboard.press('Escape')
                                    time.sleep(1)
                                    return opening_odds
                            
                            # Dacă nu găsește, încercă următorul element
                            page.keyboard.press('Escape')
                            time.sleep(1)
                            
                    except Exception as e:
                        log(f"⚠️ Eroare click element {i}: {e}")
                        continue
                        
            except Exception as e:
                log(f"⚠️ Eroare selector {selector}: {e}")
                continue
                
    except Exception as e:
        log(f"❌ Eroare extragere opening odds: {e}")
    
    return None

def find_popup_advanced(page):
    """Găsește popup-uri cu metode multiple"""
    
    popup_selectors = [
        '[class*="popup"]',
        '[class*="modal"]',
        '[class*="dialog"]',
        '[class*="tooltip"]',
        '[id*="popup"]',
        '[id*="modal"]',
        '[role="dialog"]',
        '[aria-modal="true"]',
        '.modal',
        '.popup',
        '.tooltip'
    ]
    
    for selector in popup_selectors:
        try:
            popup = page.locator(selector).first
            if popup.is_visible():
                log(f"✅ Popup găsit cu selector: {selector}")
                return popup
        except:
            continue
    
    # Verifică și elemente cu position fixed/absolute
    try:
        positioned_elements = page.locator('*').filter(has=page.locator('[style*="fixed"], [style*="absolute"]'))
        count = positioned_elements.count()
        
        for i in range(count):
            try:
                elem = positioned_elements.nth(i)
                if elem.is_visible():
                    # Verifică dacă elementul este destul de mare pentru a fi popup
                    bbox = elem.bounding_box()
                    if bbox and bbox['width'] > 100 and bbox['height'] > 50:
                        log("✅ Popup găsit prin verificare poziție")
                        return elem
            except:
                continue
    except:
        pass
    
    return None

def extract_odds_from_popup_advanced(popup):
    """Extrage cotele din popup"""
    
    try:
        popup_text = popup.inner_text()
        log(f"📝 Text popup: {popup_text[:500]}...")
        
        # Caută "Opening" sau "Initial"
        lines = popup_text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['opening', 'initial', 'open']):
                # Extrage cotele din zonă
                search_range = lines[max(0, i-2):min(len(lines), i+5)]
                search_text = '\n'.join(search_range)
                
                odds_matches = re.findall(r'\d+\.\d{2}', search_text)
                valid_odds = []
                
                for match in odds_matches:
                    odds_val = float(match)
                    if 1.0 <= odds_val <= 50.0:
                        valid_odds.append(odds_val)
                
                if len(valid_odds) >= 2:
                    return {
                        'type': 'Opening',
                        'over': valid_odds[0],
                        'under': valid_odds[1]
                    }
        
        # Fallback: primele 2 cote valide din popup
        all_odds = re.findall(r'\d+\.\d{2}', popup_text)
        valid_odds = []
        
        for match in all_odds:
            odds_val = float(match)
            if 1.0 <= odds_val <= 50.0:
                valid_odds.append(odds_val)
        
        if len(valid_odds) >= 2:
            return {
                'type': 'Opening',
                'over': valid_odds[0],
                'under': valid_odds[1]
            }
            
    except Exception as e:
        log(f"❌ Eroare extragere din popup: {e}")
    
    return None

def validate_url(url: str) -> bool:
    """Validează URL-ul OddsPortal"""
    return 'oddsportal.com' in url and '/' in url

def add_over_under_hash(url: str) -> str:
    """Adaugă #over-under;1 la URL dacă lipsește"""
    if '#over-under' not in url:
        base_url = url.split('#')[0]
        return base_url.rstrip('/') + '/#over-under;1'
    return url
