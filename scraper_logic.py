from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re
import sys
import subprocess
from typing import Optional, List, Dict

def install_playwright():
    """Instalează Playwright dacă nu este disponibil"""
    try:
        from playwright.sync_api import sync_playwright
        # Testează dacă chromium este instalat
        with sync_playwright() as p:
            p.chromium
        print("Playwright și Chromium sunt deja instalate")
    except Exception as e:
        print(f"Playwright necesită instalare: {e}")
        print("Se instalează Playwright și Chromium...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

# Verifică și instalează la import
install_playwright()

def scrape_betano_odds(match_url: str, headless: bool = True, progress_callback=None) -> Optional[List[Dict]]:
    """
    Scrape-ează cotele Betano Over/Under de pe OddsPortal
    
    Args:
        match_url: URL-ul complet al meciului
        headless: Rulează browser-ul fără UI
        progress_callback: Funcție pentru a afișa progres (ex: st.info)
    
    Returns:
        List cu dicționare: [{'type': 'Opening/Closing', 'over': float, 'under': float}]
    """
    results = []
    
    def log(msg):
        if progress_callback:
            progress_callback(msg)
    
    try:
        with sync_playwright() as p:
            # Lansează browser
            log("🌐 Se lansează browser-ul...")
            browser = p.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']  # Important pentru servere
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigare la pagină
            log("🌐 Se încarcă pagina OddsPortal...")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)  # Mărește timeout
            time.sleep(3)
            
            # Click pe tab-ul Over/Under dacă nu e deja activ
            try:
                over_under_tab = page.locator('a[href*="over-under"]').first
                if over_under_tab.is_visible():
                    over_under_tab.click()
                    time.sleep(2)
                    log("✓ Tab Over/Under activ")
            except:
                log("⚠️ Tab Over/Under posibil deja activ")
            
            # Găsește rândul Betano
            log("🔍 Caută rândul Betano...")
            betano_row = find_betano_row(page)
            
            if not betano_row:
                log("❌ Nu am putut găsi rândul Betano")
                browser.close()
                return None
            
            log("✓ Rând Betano găsit!")
            
            # Extrage cotele closing
            log("📊 Extrag cotele closing...")
            closing = extract_closing_odds(betano_row)
            
            if closing:
                results.append(closing)
                log(f"✓ Closing: Over {closing['over']} | Under {closing['under']}")
            
            # Extrage cotele opening
            log("🖱️ Click pe cotă pentru opening odds...")
            opening = extract_opening_odds(page, betano_row)
            
            if opening:
                results.append(opening)
                log(f"✓ Opening: Over {opening['over']} | Under {opening['under']}")
            
            browser.close()
            log("✅ Scraping finalizat!")
            
            return results if results else None
            
    except Exception as e:
        log(f"❌ Eroare: {str(e)}")
        return None


def find_betano_row(page):
    """Găsește rândul cu Betano în tabel"""
    try:
        # Metodă 1: Caută după text
        rows = page.locator('div[class*="eventRow"], tr, div[class*="flex-row"]').all()
        
        for row in rows:
            try:
                text = row.inner_text().lower()
                if 'betano' in text:
                    return row
            except:
                continue
        
        # Metodă 2: XPath
        betano_row = page.locator('text=/betano/i').locator('..').locator('..').first
        if betano_row.is_visible():
            return betano_row
            
    except:
        pass
    
    return None


def extract_closing_odds(betano_row) -> Optional[Dict]:
    """Extrage cotele closing (vizibile direct)"""
    try:
        # Găsește toate elementele cu cote
        odds_elements = betano_row.locator('a, span, div').all()
        
        closing_odds = []
        for elem in odds_elements:
            try:
                text = elem.inner_text().strip()
                # Verifică dacă e o cotă (format X.XX)
                if re.match(r'^\d+\.\d{2}$', text):
                    closing_odds.append(float(text))
            except:
                continue
        
        if len(closing_odds) >= 2:
            return {
                'type': 'Closing',
                'over': closing_odds[0],
                'under': closing_odds[1]
            }
    except:
        pass
    
    return None


def extract_opening_odds(page, betano_row) -> Optional[Dict]:
    """Extrage cotele opening din popup"""
    try:
        # Click pe prima cotă clickable
        clickable = betano_row.locator('a[href*="#"]').first
        
        if clickable.is_visible():
            clickable.click()
            time.sleep(2)
            
            # Caută popup-ul
            popup_selectors = [
                '[class*="popup"]',
                '[class*="tooltip"]', 
                '[class*="modal"]',
                '[id*="popup"]',
                'div[style*="position: absolute"]'
            ]
            
            popup = None
            for selector in popup_selectors:
                try:
                    popup = page.locator(selector).first
                    if popup.is_visible():
                        break
                except:
                    continue
            
            if popup and popup.is_visible():
                popup_text = popup.inner_text()
                
                # Caută "Opening" sau "Initial"
                lines = popup_text.split('\n')
                for i, line in enumerate(lines):
                    if 'opening' in line.lower() or 'initial' in line.lower():
                        # Caută cote în linia curentă sau următoarele
                        search_text = '\n'.join(lines[i:i+3])
                        odds_matches = re.findall(r'\d+\.\d{2}', search_text)
                        
                        if len(odds_matches) >= 2:
                            return {
                                'type': 'Opening',
                                'over': float(odds_matches[0]),
                                'under': float(odds_matches[1])
                            }
                
                # Fallback: extrage toate cotele din popup
                all_odds = re.findall(r'\d+\.\d{2}', popup_text)
                if len(all_odds) >= 2:
                    return {
                        'type': 'Opening',
                        'over': float(all_odds[0]),
                        'under': float(all_odds[1])
                    }
    except:
        pass
    
    return None


def validate_url(url: str) -> bool:
    """Validează URL-ul OddsPortal"""
    required_parts = [
        'oddsportal.com',
        '/'
    ]
    return all(part in url for part in required_parts)


def add_over_under_hash(url: str) -> str:
    """Adaugă #over-under;1 la URL dacă lipsește"""
    if '#over-under' not in url:
        base_url = url.split('#')[0]
        return base_url.rstrip('/') + '/#over-under;1'
    return url
