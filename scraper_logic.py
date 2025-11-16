from playwright.sync_api import sync_playwright
import time
import sys
import subprocess

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

def get_betano_over_under_odds(match_url: str, headless: bool = True):
    """
    Extrage doar liniile și cotele Over/Under de la Betano
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
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Navigare la pagina initiala
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # Verifică dacă suntem pe Over/Under
            if "#over-under" not in page.url.lower():
                print("🖱️ Se dă click pe Over/Under...")
                page.wait_for_selector('ul.visible-links.odds-tabs', timeout=10000)
                inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
                
                if inactive_over_under.count() > 0:
                    inactive_over_under.first.click()
                    time.sleep(3)
            
            # Derulează pagina
            print("📜 Se derulează pagina...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Extrage toate liniile collapsed
            print("🔍 Se extrag liniile Over/Under...")
            betano_data = []
            collapsed_rows = page.locator('[data-testid="over-under-collapsed-row"]')
            
            for i in range(collapsed_rows.count()):
                try:
                    row = collapsed_rows.nth(i)
                    
                    # Extrage linia (handicap-ul)
                    handicap_text = row.locator('[data-testid="over-under-collapsed-option-box"] p').first.inner_text()
                    handicap = handicap_text.replace("Over/Under", "").replace("O/U", "").strip()
                    
                    # Extrage cotele collapsed (cele generale)
                    over_odds = row.locator('[data-testid="odd-container-default"]:nth-child(1) p').inner_text()
                    under_odds = row.locator('[data-testid="odd-container-default"]:nth-child(2) p').inner_text()
                    
                    betano_data.append({
                        'linie': handicap,
                        'over': over_odds,
                        'under': under_odds
                    })
                    
                    print(f"📊 {handicap} | Over: {over_odds} | Under: {under_odds}")
                    
                except Exception as e:
                    print(f"⚠️ Eroare la linia {i+1}: {e}")
                    continue
            
            browser.close()
            
            if betano_data:
                print(f"✅ Extras {len(betano_data)} linii")
                return {
                    'url': page.url,
                    'data': betano_data
                }
            else:
                print("❌ Nu s-au găsit linii")
                return None
                
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        return None
