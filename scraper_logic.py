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
                    '--single-process'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Navigare la pagina initiala
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='networkidle', timeout=60000)
            time.sleep(5)  # Mai mult timp pentru încărcare
            
            # Afiseaza URL-ul initial
            initial_url = page.url
            print(f"📄 URL initial: {initial_url}")
            print(f"📄 Titlul paginii: {page.title()}")
            
            # VERIFICĂ ce tab este activ
            print("🔍 Se verifică tab-urile disponibile...")
            
            # Ia HTML-ul pentru tab-uri
            tabs_html = page.locator('ul.visible-links.odds-tabs').first.inner_html()
            print(f"📋 HTML tab-uri: {tabs_html}")
            
            # Verifică dacă suntem deja pe Over/Under
            if "#over-under" in initial_url.lower():
                print("✅ DEJA suntem pe pagina Over/Under!")
                browser.close()
                return initial_url
            
            # Caută tab-ul Over/Under (inactiv)
            print("🖱️ Se caută tab-ul Over/Under...")
            
            # Selector pentru Over/Under INACTIV (fără clasa active-odds)
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if inactive_over_under.count() > 0:
                print("✅ Over/Under găsit (inactiv) - se dă click...")
                inactive_over_under.first.click()
                print("✅ Click realizat!")
                
                # Așteaptă 5 secunde
                print("⏳ Aștept 5 secunde pentru încărcare...")
                time.sleep(5)
                
                # Capturează noul URL
                new_url = page.url
                print(f"🔄 URL nou: {new_url}")
                
                browser.close()
                return new_url
            else:
                print("❌ Over/Under nu a fost găsit ca inactiv")
                print("🔍 Se verifică toate tab-urile...")
                
                # List all tabs
                all_tabs = page.locator('[data-testid^="navigation-"]')
                tab_count = all_tabs.count()
                print(f"🔍 Număr total de tab-uri: {tab_count}")
                
                for i in range(tab_count):
                    tab = all_tabs.nth(i)
                    tab_text = tab.inner_text()
                    tab_classes = tab.get_attribute('class')
                    print(f"Tab {i+1}: '{tab_text}' - clase: {tab_classes}")
                
                browser.close()
                return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None
