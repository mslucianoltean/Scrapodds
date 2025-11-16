from playwright.sync_api import sync_playwright
import time
import sys
import subprocess
import os

def install_playwright():
    """Instalează Playwright dacă nu este disponibil"""
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright este instalat")
        
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

def extract_all_over_under_lines(match_url: str, headless: bool = True):
    """
    Extrage toate liniile Over/Under și cotele de closing
    """
    print("🌐 Se lansează browser-ul...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # Navigare direct la Over/Under
            print(f"🌐 Se încarcă pagina Over/Under: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            
            print(f"📄 Pagina încărcată: {page.title()}")
            print(f"🔗 URL curent: {page.url}")
            
            # Găsește toate liniile collapsed (cu săgeți)
            print("🔍 Se caută toate liniile Over/Under...")
            
            # Așteaptă să se încarce liniile
            page.wait_for_selector('[data-testid="over-under-collapsed-row"]', timeout=10000)
            
            # Găsește toate liniile
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            
            print(f"📊 Număr total de linii găsite: {line_count}")
            
            results = []
            
            # Parcurge fiecare linie
            for i in range(line_count):
                try:
                    line = all_lines.nth(i)
                    
                    # Extrage textul liniei (handicap-ul)
                    line_text = line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
                    print(f"📝 Linia {i+1}: {line_text}")
                    
                    # Dă click pe săgeată pentru a deschide linia
                    arrow = line.locator('.bg-provider-arrow').first
                    if arrow.is_visible():
                        print(f"🖱️ Se dă click pe săgeata liniei {i+1}...")
                        arrow.click()
                        time.sleep(2)  # Așteaptă să se deschidă
                        
                        # Acum că linia este deschisă, caută Betano
                        betano_row = find_betano_in_expanded_row(page)
                        
                        if betano_row:
                            # Extrage cotele de closing de la Betano
                            odds = extract_closing_odds_from_betano(betano_row)
                            if odds:
                                results.append({
                                    'line': line_text,
                                    'over': odds['over'],
                                    'under': odds['under']
                                })
                                print(f"✅ Betano găsit - Over: {odds['over']}, Under: {odds['under']}")
                            else:
                                print(f"❌ Nu s-au putut extrage cotele de la Betano pentru {line_text}")
                        else:
                            print(f"❌ Betano nu a fost găsit pentru {line_text}")
                        
                        # Închide linia dând click din nou pe săgeată
                        arrow.click()
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️ Eroare la linia {i+1}: {e}")
                    continue
            
            browser.close()
            
            if results:
                print(f"🎉 Extracție finalizată! {len(results)} linii cu Betano găsite")
                return results
            else:
                print("❌ Nu s-au găsit date Betano")
                return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None

def find_betano_in_expanded_row(page):
    """
    Caută rândul Betano în linia deschisă
    """
    try:
        # Caută rândurile expandate (după ce s-a dat click pe săgeată)
        expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
        
        for i in range(expanded_rows.count()):
            row = expanded_rows.nth(i)
            if row.is_visible():
                row_text = row.inner_text()
                if 'Betano' in row_text:
                    print("✅ Betano găsit în rândul expandat!")
                    return row
                    
        # Fallback: caută prin logo/text
        betano_selectors = [
            'img[alt="Betano.ro"]',
            'text=Betano.ro',
            '[class*="betano"]',
            '[src*="betano"]'
        ]
        
        for selector in betano_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    print(f"✅ Betano găsit cu selector: {selector}")
                    # Navighează la containerul părinte
                    betano_row = element.locator('xpath=./ancestor::div[@data-testid="over-under-expanded-row"]').first
                    if betano_row.is_visible():
                        return betano_row
            except:
                continue
                
        return None
        
    except Exception as e:
        print(f"❌ Eroare la căutarea Betano: {e}")
        return None

def extract_closing_odds_from_betano(betano_row):
    """
    Extrage cotele de closing de la Betano
    """
    try:
        # Caută containerele de cote
        odds_containers = betano_row.locator('[data-testid="odd-container"]')
        
        if odds_containers.count() >= 2:
            # Primul container este pentru Over
            over_container = odds_containers.nth(0)
            over_text = over_container.locator('[data-testid="odd-container-default"]').first.inner_text().strip()
            
            # Al doilea container este pentru Under
            under_container = odds_containers.nth(1)
            under_text = under_container.locator('[data-testid="odd-container-default"]').first.inner_text().strip()
            
            try:
                over_odds = float(over_text) if over_text != '-' else None
                under_odds = float(under_text) if under_text != '-' else None
                
                return {
                    'over': over_odds,
                    'under': under_odds
                }
            except ValueError:
                print(f"⚠️ Cote invalide: Over='{over_text}', Under='{under_text}'")
                return None
        
        return None
        
    except Exception as e:
        print(f"❌ Eroare la extragerea coteLOR: {e}")
        return None
