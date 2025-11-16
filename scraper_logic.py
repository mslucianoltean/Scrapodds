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
        # Testează dacă Playwright este instalat
        from playwright.sync_api import sync_playwright
        
        # Testează dacă chromium este disponibil
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, timeout=10000)
                browser.close()
            print("✓ Playwright și Chromium sunt funcționale")
        except Exception as e:
            print(f"⚠️ Chromium necesită instalare: {e}")
            print("📥 Se instalează browserele Playwright...")
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
    
    try:
        with sync_playwright() as p:
            log("🌐 Se lansează browser-ul Chromium...")
            
            # Opțiuni de launch pentru medii server
            launch_options = {
                'headless': headless,
                'timeout': 30000
            }
            
            # Adaugă argumente specifice pentru medii server
            if os.environ.get('STREAMLIT_SHARED_MODE') or os.environ.get('SERVER_ENVIRONMENT'):
                launch_options['args'] = [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            
            browser = p.chromium.launch(**launch_options)
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # Navigare la pagină cu timeout crescut
            log("🌐 Se încarcă pagina OddsPortal...")
            page.goto(match_url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            # Încearcă să găsească și să click-uieste pe tab-ul Over/Under
            log("🔍 Se caută tab-ul Over/Under...")
            over_under_selectors = [
                'a[href*="over-under"]',
                '//a[contains(text(), "Over/Under")]',
                '//a[contains(text(), "O/U")]',
                '[class*="over-under"]'
            ]
            
            tab_found = False
            for selector in over_under_selectors:
                try:
                    if selector.startswith('//'):
                        tab = page.locator(f"xpath={selector}").first
                    else:
                        tab = page.locator(selector).first
                    
                    if tab.is_visible():
                        tab.click()
                        time.sleep(2)
                        log("✓ Tab Over/Under activat")
                        tab_found = True
                        break
                except:
                    continue
            
            if not tab_found:
                log("ℹ️ Tab Over/Under nu a fost găsit sau este deja activ")
            
            # Așteaptă încărcarea conținutului
            time.sleep(3)
            
            # Găsește rândul Betano
            log("🔍 Se caută rândul Betano...")
            betano_row = find_betano_row(page)
            
            if not betano_row:
                log("❌ Nu s-a putut găsi rândul Betano")
                # Screenshot pentru debugging
                try:
                    page.screenshot(path="/tmp/debug_page.png")
                    log("📸 Screenshot salvat pentru debugging")
                except:
                    pass
                browser.close()
                return None
            
            log("✓ Rând Betano găsit!")
            
            # Extrage cotele closing
            log("📊 Se extrag cotele closing...")
            closing = extract_closing_odds(betano_row)
            
            if closing:
                results.append(closing)
                log(f"✓ Closing: Over {closing['over']} | Under {closing['under']}")
            else:
                log("❌ Nu s-au putut extrage cotele closing")
            
            # Extrage cotele opening
            log("🖱️ Se încearcă extragerea opening odds...")
            opening = extract_opening_odds(page, betano_row)
            
            if opening:
                results.append(opening)
                log(f"✓ Opening: Over {opening['over']} | Under {opening['under']}")
            else:
                log("ℹ️ Nu s-au putut extrage opening odds")
            
            browser.close()
            
            if results:
                log("✅ Scraping finalizat cu succes!")
                return results
            else:
                log("❌ Nu s-au putut extrage date")
                return None
            
    except Exception as e:
        log(f"❌ Eroare la scraping: {str(e)}")
        return None

def find_betano_row(page):
    """Găsește rândul cu Betano în tabel"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Metodă 1: Caută direct textul Betano
            betano_selector = page.locator('text=/betano/i')
            if betano_selector.count() > 0:
                # Navighează în sus în ierarhie pentru a găsi rândul
                row = betano_selector.locator('xpath=./ancestor::tr | ./ancestor::div[contains(@class, "row")] | ./ancestor::div[contains(@class, "eventRow")]').first
                if row.is_visible():
                    return row
            
            # Metodă 2: Caută în toate rândurile
            rows = page.locator('tr, div[class*="eventRow"], div[class*="flex-row"], div[class*="row"]').all()
            
            for row in rows:
                try:
                    if row.is_visible():
                        text = row.inner_text().lower()
                        if 'betano' in text:
                            return row
                except:
                    continue
            
            # Metodă 3: XPath mai agresiv
            xpath_selectors = [
                '//*[contains(text(), "Betano") or contains(text(), "betano")]/ancestor::tr[1]',
                '//*[contains(text(), "Betano") or contains(text(), "betano")]/ancestor::div[contains(@class, "row")][1]',
                '//tr[.//*[contains(text(), "Betano") or contains(text(), "betano")]]'
            ]
            
            for xpath in xpath_selectors:
                try:
                    row = page.locator(f"xpath={xpath}").first
                    if row.is_visible():
                        return row
                except:
                    continue
            
            # Dacă nu găsește, așteaptă și reîncearcă
            if attempt < max_retries - 1:
                time.sleep(2)
                page.reload()
                time.sleep(3)
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    return None

def extract_closing_odds(betano_row) -> Optional[Dict]:
    """Extrage cotele closing (vizibile direct)"""
    try:
        # Găsește toate elementele care ar putea conține cote
        odds_selectors = [
            'a',
            'span',
            'div',
            'button',
            '* >> text=/^\\d+\\.\\d{2}$/'
        ]
        
        closing_odds = []
        
        for selector in odds_selectors:
            try:
                elements = betano_row.locator(selector).all()
                for elem in elements:
                    try:
                        text = elem.inner_text().strip()
                        # Verifică dacă e o cotă (format X.XX)
                        if re.match(r'^\d+\.\d{2}$', text):
                            closing_odds.append(float(text))
                            if len(closing_odds) >= 2:
                                break
                    except:
                        continue
                if len(closing_odds) >= 2:
                    break
            except:
                continue
        
        if len(closing_odds) >= 2:
            return {
                'type': 'Closing',
                'over': closing_odds[0],
                'under': closing_odds[1]
            }
        
        # Fallback: extrage toate numerele din textul rândului
        row_text = betano_row.inner_text()
        all_odds = re.findall(r'\d+\.\d{2}', row_text)
        if len(all_odds) >= 2:
            return {
                'type': 'Closing',
                'over': float(all_odds[0]),
                'under': float(all_odds[1])
            }
            
    except Exception as e:
        print(f"Eroare la extragerea closing odds: {e}")
    
    return None

def extract_opening_odds(page, betano_row) -> Optional[Dict]:
    """Extrage cotele opening din popup"""
    try:
        # Găsește elemente clickable în rândul Betano
        clickable_selectors = [
            'a',
            'button',
            '[onclick]',
            '[class*="click"]',
            '[class*="odds"]'
        ]
        
        for selector in clickable_selectors:
            try:
                clickable_elements = betano_row.locator(selector).all()
                for elem in clickable_elements:
                    if elem.is_visible():
                        # Salvează starea curentă a paginii
                        original_url = page.url
                        
                        # Încearcă click
                        elem.click()
                        time.sleep(2)
                        
                        # Caută popup-ul sau tooltip-ul
                        popup = find_popup(page)
                        if popup:
                            opening_odds = extract_odds_from_popup(popup)
                            if opening_odds:
                                # Închide popup-ul făcând click în altă parte
                                page.mouse.click(10, 10)
                                time.sleep(1)
                                return opening_odds
                        
                        # Dacă nu găsește, revine la URL-ul original
                        if page.url != original_url:
                            page.goto(original_url)
                            time.sleep(2)
                            
            except:
                continue
                
    except Exception as e:
        print(f"Eroare la extragerea opening odds: {e}")
    
    return None

def find_popup(page):
    """Găsește popup-ul sau tooltip-ul"""
    popup_selectors = [
        '[class*="popup"]',
        '[class*="tooltip"]',
        '[class*="modal"]',
        '[id*="popup"]',
        '[id*="tooltip"]',
        '[class*="dialog"]',
        'div[style*="absolute"]',
        'div[style*="fixed"]',
        '[role="dialog"]',
        '[aria-modal="true"]'
    ]
    
    for selector in popup_selectors:
        try:
            popup = page.locator(selector).first
            if popup.is_visible():
                return popup
        except:
            continue
    
    return None

def extract_odds_from_popup(popup):
    """Extrage cotele din popup"""
    try:
        popup_text = popup.inner_text()
        
        # Caută "Opening" sau "Initial"
        lines = popup_text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['opening', 'initial', 'open', 'open odds']):
                # Caută cote în liniile din jur
                search_range = lines[max(0, i-2):min(len(lines), i+5)]
                search_text = '\n'.join(search_range)
                odds_matches = re.findall(r'\d+\.\d{2}', search_text)
                
                if len(odds_matches) >= 2:
                    return {
                        'type': 'Opening',
                        'over': float(odds_matches[0]),
                        'under': float(odds_matches[1])
                    }
        
        # Fallback: extrage primele 2 cote din popup
        all_odds = re.findall(r'\d+\.\d{2}', popup_text)
        if len(all_odds) >= 2:
            return {
                'type': 'Opening',
                'over': float(all_odds[0]),
                'under': float(all_odds[1])
            }
            
    except Exception as e:
        print(f"Eroare la extragerea din popup: {e}")
    
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
