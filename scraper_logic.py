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
    Extrage toate liniile Over/Under cu derulare pentru lazy loading
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
                viewport={'width': 1920, 'height': 2000},  # Mai înalt pentru derulare
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # PASUL 1: Navigare la home/away
            print(f"🌐 Se încarcă pagina inițială: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            print(f"📄 Pagina încărcată: {page.title()}")
            print(f"🔗 URL curent: {page.url}")
            
            # PASUL 2: Dă click pe Over/Under
            print("🖱️ Se dă click pe tab-ul Over/Under...")
            
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if inactive_over_under.count() > 0 and inactive_over_under.first.is_visible():
                inactive_over_under.first.click()
                print("✅ Click realizat pe Over/Under!")
                
                # Așteaptă să se încarce liniile
                print("⏳ Se așteaptă încărcarea liniilor Over/Under...")
                time.sleep(5)
                
                # PASUL 3: DERULEAZĂ pentru a încărca toate liniile (lazy loading)
                print("🔄 Se derulează pentru a încărca toate liniile...")
                
                # Derulează de mai multe ori pentru a încărca toate liniile
                for scroll_attempt in range(5):
                    # Derulează până jos
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    
                    # Verifică câte linii sunt acum
                    current_lines = page.locator('[data-testid="over-under-collapsed-row"]')
                    current_count = current_lines.count()
                    print(f"📊 După derulare {scroll_attempt + 1}: {current_count} linii")
                    
                    # Dacă nu se mai încarcă linii noi, oprește-te
                    if scroll_attempt > 0:
                        previous_count = page.locator('[data-testid="over-under-collapsed-row"]').count()
                        if current_count == previous_count:
                            print("✅ Nu se mai încarcă linii noi - derulare oprită")
                            break
                
                # Așteaptă un pic după derulare
                time.sleep(3)
                
                # PASUL 4: Extrage toate liniile
                all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
                line_count = all_lines.count()
                
                print(f"🎯 TOTAL linii găsite: {line_count}")
                
                # Extrage toate liniile
                results = []
                
                for i in range(line_count):
                    try:
                        line = all_lines.nth(i)
                        
                        # Extrage textul liniei
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
                    print(f"🎉 EXTRACȚIE COMPLETĂ! {len(results)} linii găsite")
                    return results
                else:
                    print("❌ Nu s-au găsit linii")
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
