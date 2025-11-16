from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re
import sys
import subprocess
import os
import base64
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
    Scrape-ează cotele Betano Over/Under de pe OddsPortal - Versiune optimizată
    """
    results = []
    
    def log(msg):
        if progress_callback:
            progress_callback(msg)
        print(f"LOG: {msg}")
    
    # Forțează headless pe servere
    if os.environ.get('STREAMLIT_SHARED_MODE'):
        headless = True
        log("🔧 Mod headless forțat pentru mediu server")
    
    try:
        with sync_playwright() as p:
            log("🌐 Se lansează browser-ul...")
            
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Navigare la pagină
            log("🌐 Se încarcă pagina OddsPortal...")
            page.goto(match_url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            # Verifică dacă suntem pe pagina corectă
            if 'oddsportal.com' not in page.url:
                log("❌ Nu suntem pe OddsPortal")
                browser.close()
                return None
            
            log(f"📄 Pagina încărcată: {page.title()}")
            
            # Așteaptă încărcarea conținutului
            log("⏳ Se așteaptă încărcarea datelor...")
            time.sleep(5)
            
            # Încearcă să găsească Betano folosind metode multiple
            betano_data = find_betano_data(page)
            
            if not betano_data:
                log("❌ Betano nu a fost găsit sau nu are cote pentru acest meci")
                browser.close()
                return None
            
            log("✅ Date Betano găsite!")
            
            # Extrage cotele
            closing_odds = extract_closing_odds_from_data(betano_data)
            if closing_odds:
                results.append(closing_odds)
                log(f"✅ Closing: Over {closing_odds['over']} | Under {closing_odds['under']}")
            
            # Încearcă să găsească opening odds
            opening_odds = extract_opening_odds_from_data(betano_data, page)
            if opening_odds:
                results.append(opening_odds)
                log(f"✅ Opening: Over {opening_odds['over']} | Under {opening_odds['under']}")
            
            browser.close()
            
            if results:
                log("🎉 Scraping finalizat cu succes!")
                return results
            else:
                log("❌ Nu s-au putut extrage cotele")
                return None
            
    except Exception as e:
        log(f"❌ Eroare critică: {str(e)}")
        return None

def find_betano_data(page):
    """Găsește datele Betano folosind metode multiple"""
    
    # Metoda 1: Caută în structura de date a paginii
    try:
        # Încearcă să găsească script-uri care conțin date
        scripts = page.locator('script').all()
        for script in scripts:
            try:
                content = script.inner_text()
                if 'Betano' in content and ('over' in content.lower() or 'under' in content.lower()):
                    log("✅ Betano găsit în script-uri")
                    return {'type': 'script', 'content': content}
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare la scanarea script-urilor: {e}")
    
    # Metoda 2: Caută în elementele vizuale
    try:
        # Selectori pentru OddsPortal modern
        selectors = [
            'div[data-bookmaker*="betano"]',
            '[class*="betano"]',
            'tr:has-text("Betano")',
            'div:has-text("Betano")',
            '//*[contains(text(), "Betano")]'
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('//'):
                    element = page.locator(f"xpath={selector}").first
                else:
                    element = page.locator(selector).first
                
                if element.is_visible():
                    log(f"✅ Betano găsit cu selector: {selector}")
                    return {'type': 'element', 'element': element}
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare la scanarea elementelor: {e}")
    
    # Metoda 3: Caută în tot textul paginii
    try:
        page_text = page.inner_text('body')
        if 'Betano' in page_text:
            log("✅ Betano găsit în textul paginii")
            return {'type': 'page_text', 'content': page_text}
    except Exception as e:
        log(f"⚠️ Eroare la scanarea textului paginii: {e}")
    
    return None

def extract_closing_odds_from_data(betano_data):
    """Extrage cotele closing din datele găsite"""
    
    try:
        if betano_data['type'] == 'element':
            element = betano_data['element']
            text = element.inner_text()
            
            # Extrage toate numerele care arată a cote
            odds = re.findall(r'\d+\.\d{2}', text)
            valid_odds = []
            
            for odd in odds:
                odd_float = float(odd)
                if 1.0 < odd_float < 50.0:  # Cote normale pentru sport
                    valid_odds.append(odd_float)
            
            if len(valid_odds) >= 2:
                return {
                    'type': 'Closing',
                    'over': valid_odds[0],
                    'under': valid_odds[1]
                }
        
        elif betano_data['type'] in ['script', 'page_text']:
            text = betano_data['content']
            
            # Caută pattern-uri specifice pentru cote
            patterns = [
                r'(\d+\.\d{2}).*?(\d+\.\d{2})',  # Două cote consecutive
                r'over.*?(\d+\.\d{2}).*?under.*?(\d+\.\d{2})',
                r'(\d+\.\d{2}).*?over.*?(\d+\.\d{2}).*?under'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        try:
                            over = float(match[0])
                            under = float(match[1])
                            if 1.0 < over < 50.0 and 1.0 < under < 50.0:
                                return {
                                    'type': 'Closing',
                                    'over': over,
                                    'under': under
                                }
                        except:
                            continue
            
            # Fallback: primele 2 cote valide găsite
            odds = re.findall(r'\d+\.\d{2}', text)
            valid_odds = []
            
            for odd in odds:
                odd_float = float(odd)
                if 1.0 < odd_float < 50.0:
                    valid_odds.append(odd_float)
            
            if len(valid_odds) >= 2:
                return {
                    'type': 'Closing',
                    'over': valid_odds[0],
                    'under': valid_odds[1]
                }
                
    except Exception as e:
        log(f"❌ Eroare la extragerea closing odds: {e}")
    
    return None

def extract_opening_odds_from_data(betano_data, page):
    """Extrage opening odds"""
    
    try:
        # Pentru opening odds, trebuie să facem click pe element
        if betano_data['type'] == 'element':
            element = betano_data['element']
            
            # Găsește elemente clickable în apropiere
            clickable = element.locator('a, button, [onclick]').first
            if clickable.is_visible():
                clickable.click()
                time.sleep(2)
                
                # Caută popup-ul sau tooltip-ul
                popup_selectors = [
                    '[class*="tooltip"]',
                    '[class*="popup"]',
                    '[class*="modal"]',
                    '[style*="absolute"]',
                    '[style*="fixed"]'
                ]
                
                for selector in popup_selectors:
                    try:
                        popup = page.locator(selector).first
                        if popup.is_visible():
                            popup_text = popup.inner_text()
                            
                            # Caută "opening" în text
                            if 'opening' in popup_text.lower():
                                odds = re.findall(r'\d+\.\d{2}', popup_text)
                                valid_odds = []
                                
                                for odd in odds:
                                    odd_float = float(odd)
                                    if 1.0 < odd_float < 50.0:
                                        valid_odds.append(odd_float)
                                
                                if len(valid_odds) >= 2:
                                    # Închide popup-ul
                                    page.keyboard.press('Escape')
                                    return {
                                        'type': 'Opening',
                                        'over': valid_odds[0],
                                        'under': valid_odds[1]
                                    }
                    except:
                        continue
                
                # Închide orice popup deschis
                page.keyboard.press('Escape')
                
    except Exception as e:
        log(f"⚠️ Eroare la extragerea opening odds: {e}")
    
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
