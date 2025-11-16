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

def click_over_under_and_get_url(match_url: str, headless: bool = True):
    """
    Dă click pe tab-ul Over/Under și returnează noul URL
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
            
            # Navigare la pagina initiala
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            
            # Afiseaza URL-ul initial
            initial_url = page.url
            print(f"📄 URL initial: {initial_url}")
            print(f"📄 Titlul paginii: {page.title()}")
            
            # VERIFICĂ dacă suntem deja pe Over/Under
            if "#over-under" in initial_url.lower():
                print("✅ DEJA suntem pe pagina Over/Under!")
                browser.close()
                return initial_url
            
            print("🖱️ Se caută tab-ul Over/Under...")
            
            # Așteaptă să se încarce tab-urile
            page.wait_for_selector('ul.visible-links.odds-tabs', timeout=10000)
            
            # Caută tab-ul Over/Under INACTIV
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if inactive_over_under.count() > 0 and inactive_over_under.first.is_visible():
                print("✅ Over/Under găsit (inactiv) - se dă click...")
                inactive_over_under.first.click()
                print("✅ Click realizat!")
                
                # Așteaptă 5 secunde pentru încărcare
                print("⏳ Aștept 5 secunde pentru încărcare...")
                time.sleep(5)
                
                # Capturează noul URL
                new_url = page.url
                print(f"🔄 URL nou: {new_url}")
                
                browser.close()
                return new_url
            else:
                print("❌ Over/Under nu a fost găsit ca inactiv")
                
                # Debug: afișează toate tab-urile
                all_tabs = page.locator('[data-testid^="navigation-"]')
                tab_count = all_tabs.count()
                print(f"🔍 Număr total de tab-uri: {tab_count}")
                
                for i in range(tab_count):
                    tab = all_tabs.nth(i)
                    if tab.is_visible():
                        tab_text = tab.inner_text()
                        is_active = "active-odds" in tab.get_attribute('class') or ""
                        print(f"Tab {i+1}: '{tab_text}' - activ: {is_active}")
                
                browser.close()
                return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None
