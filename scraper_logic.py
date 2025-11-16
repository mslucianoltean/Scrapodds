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

def test_sageti_si_betano(match_url: str, headless: bool = True):
    """
    TEST: Verifică dacă săgețile funcționează și găsește Betano
    """
    print("🌐 TEST - Se lansează browser-ul...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-web-security'
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 2000},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # Navigare la home/away + click pe Over/Under
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # Click pe Over/Under
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                print("✅ Click pe Over/Under!")
                time.sleep(5)
            
            # Derulează pentru toate liniile
            print("🔄 Se derulează pentru toate liniile...")
            for scroll_attempt in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            time.sleep(3)
            
            # Găsește toate liniile
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            print(f"📊 Total linii pentru test: {line_count}")
            
            results = []
            
            # TEST: Primele 3 linii pentru a verifica săgețile și Betano
            for i in range(min(3, line_count)):
                try:
                    line = all_lines.nth(i)
                    line_text = line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
                    print(f"\n🔍 TEST Linia {i+1}: {line_text}")
                    
                    # Găsește săgeata
                    arrow = line.locator('.bg-provider-arrow').first
                    if arrow.is_visible():
                        print(f"   ✅ Săgeată găsită - se dă click...")
                        arrow.click()
                        time.sleep(3)  # Așteaptă să se deschidă
                        
                        # Acum că linia este deschisă, caută Betano
                        betano_found = find_betano_in_page(page)
                        
                        if betano_found:
                            print(f"   ✅ BETANO GĂSIT! - {betano_found}")
                            
                            # Încearcă să extragi cotele
                            odds = extract_odds_from_betano(page)
                            if odds:
                                print(f"   ✅ Cote găsite: Over={odds['over']}, Under={odds['under']}")
                                results.append({
                                    'line': line_text,
                                    'betano': 'DA',
                                    'over': odds['over'],
                                    'under': odds['under']
                                })
                            else:
                                print(f"   ⚠️ Betano găsit dar cotele nu s-au putut extrage")
                                results.append({
                                    'line': line_text,
                                    'betano': 'DA (fără cote)',
                                    'over': 'N/A',
                                    'under': 'N/A'
                                })
                        else:
                            print(f"   ❌ Betano NU a fost găsit")
                            results.append({
                                'line': line_text,
                                'betano': 'NU',
                                'over': 'N/A', 
                                'under': 'N/A'
                            })
                        
                        # Închide linia dând click din nou
                        arrow.click()
                        time.sleep(1)
                    else:
                        print(f"   ❌ Săgeată NU a fost găsită")
                        results.append({
                            'line': line_text,
                            'betano': 'NU (fără săgeată)',
                            'over': 'N/A',
                            'under': 'N/A'
                        })
                        
                except Exception as e:
                    print(f"⚠️ Eroare la TEST linia {i+1}: {e}")
                    results.append({
                        'line': f"Linia {i+1} - EROARE",
                        'betano': f"Eroare: {str(e)}",
                        'over': 'N/A',
                        'under': 'N/A'
                    })
                    continue
            
            browser.close()
            
            print(f"\n🎯 REZULTATE TEST:")
            for result in results:
                print(f"   {result['line']} -> Betano: {result['betano']}")
            
            return results
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None

def find_betano_in_page(page):
    """
    Caută Betano în pagina curentă folosind mai multe metode
    """
    try:
        # Metoda 1: După textul "Betano.ro"
        betano_text = page.locator('text=Betano.ro').first
        if betano_text.is_visible():
            return "Găsit prin text"
        
        # Metoda 2: După data-testid (dacă există)
        betano_testid = page.locator('[data-testid*="betano"]').first
        if betano_testid.count() > 0 and betano_testid.first.is_visible():
            return "Găsit prin data-testid"
        
        # Metoda 3: După class care conține "betano"
        betano_class = page.locator('[class*="betano"]').first
        if betano_class.count() > 0 and betano_class.first.is_visible():
            return "Găsit prin class"
        
        # Metoda 4: Verifică HTML-ul pentru Betano
        page_html = page.content()
        if 'Betano.ro' in page_html:
            return "Betano în HTML dar nu vizibil"
        
        return "Negăsit"
        
    except Exception as e:
        return f"Eroare căutare: {str(e)}"

def extract_odds_from_betano(page):
    """
    Încearcă să extragă cotele de la Betano
    """
    try:
        # Caută containerele de cote lângă Betano
        # Aceasta va trebui ajustată după ce vedem structura exactă
        odds_containers = page.locator('[data-testid="odd-container"]')
        
        if odds_containers.count() >= 2:
            over_text = odds_containers.nth(0).inner_text().strip()
            under_text = odds_containers.nth(1).inner_text().strip()
            
            return {
                'over': over_text,
                'under': under_text
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Eroare extragere cote: {e}")
        return None
