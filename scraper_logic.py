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
    Scrape-ează cotele Betano Over/Under de pe OddsPortal - Versiune corectă
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
            
            # Găsește Betano folosind selectori exacte bazate pe structura HTML
            betano_row = find_betano_row_exact(page)
            
            if not betano_row:
                log("❌ Betano nu a fost găsit")
                browser.close()
                return None
            
            log("✅ Betano găsit! Se extrag cotele...")
            
            # Extrage cotele closing
            closing_odds = extract_closing_odds_exact(betano_row)
            if closing_odds:
                results.append(closing_odds)
                log(f"✅ Closing: Over {closing_odds['over']} | Under {closing_odds['under']}")
            else:
                log("❌ Nu s-au putut extrage cotele closing")
            
            # Încearcă să găsească opening odds
            opening_odds = extract_opening_odds_exact(page, betano_row)
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
                log("❌ Nu s-au putut extrage cotele")
                return None
            
    except Exception as e:
        log(f"❌ Eroare critică: {str(e)}")
        import traceback
        log(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None

def find_betano_row_exact(page):
    """Găsește rândul Betano folosind selectori exacte bazate pe structura HTML"""
    
    # Metoda 1: Caută după logo-ul Betano
    try:
        betano_logo = page.locator('img[alt="Betano.ro"]').first
        if betano_logo.is_visible():
            log("✅ Betano găsit prin logo")
            # Navighează la containerul părinte care conține toate datele
            betano_container = betano_logo.locator('xpath=./ancestor::div[@data-testid="over-under-expanded-row"]').first
            if betano_container.is_visible():
                return betano_container
    except Exception as e:
        log(f"⚠️ Eroare la găsirea logo-ului: {e}")
    
    # Metoda 2: Caută după textul "Betano.ro"
    try:
        betano_text = page.locator('text=Betano.ro').first
        if betano_text.is_visible():
            log("✅ Betano găsit prin text")
            betano_container = betano_text.locator('xpath=./ancestor::div[@data-testid="over-under-expanded-row"]').first
            if betano_container.is_visible():
                return betano_container
    except Exception as e:
        log(f"⚠️ Eroare la găsirea textului: {e}")
    
    # Metoda 3: Caută în toate rândurile de date
    try:
        all_rows = page.locator('[data-testid="over-under-expanded-row"]')
        row_count = all_rows.count()
        log(f"🔍 Total rânduri găsite: {row_count}")
        
        for i in range(row_count):
            try:
                row = all_rows.nth(i)
                if row.is_visible():
                    row_text = row.inner_text()
                    if 'Betano' in row_text:
                        log(f"✅ Betano găsit în rândul {i+1}")
                        return row
            except:
                continue
    except Exception as e:
        log(f"⚠️ Eroare la scanarea rândurilor: {e}")
    
    return None

def extract_closing_odds_exact(betano_row):
    """Extrage cotele closing din rândul Betano"""
    
    try:
        # Găsește containerele de cote folosind data-testid exact
        odds_containers = betano_row.locator('[data-testid="odd-container"]')
        odds_count = odds_containers.count()
        log(f"🔍 Containere de cote găsite: {odds_count}")
        
        if odds_count >= 2:
            # Primul container este pentru Over
            over_container = odds_containers.nth(0)
            over_text = over_container.locator('.odds-text').first.inner_text().strip()
            
            # Al doilea container este pentru Under
            under_container = odds_containers.nth(1)
            under_text = under_container.locator('.odds-text').first.inner_text().strip()
            
            try:
                over_odds = float(over_text)
                under_odds = float(under_text)
                
                log(f"📊 Cote brute: Over={over_text}, Under={under_text}")
                
                return {
                    'type': 'Closing',
                    'over': over_odds,
                    'under': under_odds
                }
            except ValueError as e:
                log(f"❌ Eroare la conversia coteLOR: {e}")
                return None
        
        # Fallback: caută cote în textul rândului
        row_text = betano_row.inner_text()
        log(f"📝 Text rând: {row_text[:200]}...")
        
        # Caută pattern-uri de cote în text
        odds_pattern = r'(\d+\.\d{2})'
        all_odds = re.findall(odds_pattern, row_text)
        log(f"🔢 Toate cotele găsite în text: {all_odds}")
        
        # Filtrează cote valide (între 1.0 și 50.0)
        valid_odds = []
        for odd in all_odds:
            try:
                odd_float = float(odd)
                if 1.0 < odd_float < 50.0:
                    valid_odds.append(odd_float)
            except:
                continue
        
        if len(valid_odds) >= 2:
            return {
                'type': 'Closing',
                'over': valid_odds[0],
                'under': valid_odds[1]
            }
            
    except Exception as e:
        log(f"❌ Eroare la extragerea coteLOR: {e}")
    
    return None

def extract_opening_odds_exact(page, betano_row):
    """Extrage opening odds făcând click pe cote"""
    
    try:
        # Găsește primele containere de cote clickable
        odds_containers = betano_row.locator('[data-testid="odd-container"]')
        
        if odds_containers.count() >= 1:
            # Încearcă să faci click pe prima cotă
            first_odds = odds_containers.nth(0)
            
            if first_odds.is_visible():
                log("🖱️ Se încearcă click pe cotă pentru opening odds...")
                first_odds.click()
                time.sleep(2)
                
                # Caută popup-ul sau tooltip-ul care apare
                popup_selectors = [
                    '[class*="tooltip"]',
                    '[class*="popup"]',
                    '[class*="modal"]',
                    '[style*="absolute"]',
                    '[style*="fixed"]',
                    '[role="tooltip"]'
                ]
                
                for selector in popup_selectors:
                    try:
                        popup = page.locator(selector).first
                        if popup.is_visible():
                            popup_text = popup.inner_text()
                            log(f"📋 Text popup: {popup_text[:100]}...")
                            
                            # Caută "opening" în textul popup-ului
                            if 'opening' in popup_text.lower():
                                log("✅ Opening odds găsite în popup!")
                                
                                # Extrage cotele din popup
                                odds_pattern = r'(\d+\.\d{2})'
                                popup_odds = re.findall(odds_pattern, popup_text)
                                valid_odds = []
                                
                                for odd in popup_odds:
                                    try:
                                        odd_float = float(odd)
                                        if 1.0 < odd_float < 50.0:
                                            valid_odds.append(odd_float)
                                    except:
                                        continue
                                
                                if len(valid_odds) >= 2:
                                    # Închide popup-ul
                                    page.keyboard.press('Escape')
                                    time.sleep(1)
                                    return {
                                        'type': 'Opening',
                                        'over': valid_odds[0],
                                        'under': valid_odds[1]
                                    }
                    except:
                        continue
                
                # Închide orice popup deschis
                page.keyboard.press('Escape')
                time.sleep(1)
                
    except Exception as e:
        log(f"⚠️ Eroare la extragerea opening odds: {e}")
        # Închide orice popup deschis în caz de eroare
        try:
            page.keyboard.press('Escape')
        except:
            pass
    
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
