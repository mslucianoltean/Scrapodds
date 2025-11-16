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
    Extrage toate liniile Over/Under pornind de la home/away
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
                    '--disable-web-security'
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # PASUL 1: Navigare la home/away (care știm că funcționează)
            print(f"🌐 Se încarcă pagina inițială: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            print(f"📄 Pagina încărcată: {page.title()}")
            print(f"🔗 URL curent: {page.url}")
            
            # PASUL 2: Dă click pe Over/Under (așa cum am făcut în test)
            print("🖱️ Se dă click pe tab-ul Over/Under...")
            
            # Folosim același selector care a funcționat
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if inactive_over_under.count() > 0 and inactive_over_under.first.is_visible():
                inactive_over_under.first.click()
                print("✅ Click realizat pe Over/Under!")
                
                # Așteaptă să se încarce liniile
                print("⏳ Se așteaptă încărcarea liniilor Over/Under...")
                time.sleep(5)
                
                # Verifică noul URL
                new_url = page.url
                print(f"🔄 URL nou: {new_url}")
                
                # PASUL 3: Acum că suntem pe Over/Under, extragem liniile
                print("🔍 Se caută liniile cu săgeți...")
                
                # Așteaptă să se încarce liniile
                page.wait_for_selector('[data-testid="over-under-collapsed-row"]', timeout=10000)
                
                # Găsește toate liniile
                all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
                line_count = all_lines.count()
                
                print(f"📊 Număr total de linii găsite: {line_count}")
                
                # Extrage doar informațiile de bază pentru început (fără să dăm click pe săgeți)
                results = []
                
                for i in range(min(line_count, 5)):  # Testează doar primele 5 linii
                    try:
                        line = all_lines.nth(i)
                        
                        # Extrage textul liniei (handicap-ul)
                        line_text = line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
                        print(f"📝 Linia {i+1}: {line_text}")
                        
                        results.append({
                            'line': line_text,
                            'over': 'N/A',
                            'under': 'N/A'
                        })
                        
                    except Exception as e:
                        print(f"⚠️ Eroare la linia {i+1}: {e}")
                        continue
                
                browser.close()
                
                if results:
                    print(f"🎉 DEBUG - {len(results)} linii găsite!")
                    return results
                else:
                    print("❌ DEBUG - Nu s-au găsit linii")
                    return None
            else:
                print("❌ Nu s-a putut da click pe Over/Under")
                browser.close()
                return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None
