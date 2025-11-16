from playwright.sync_api import sync_playwright
import time
import sys
import subprocess

def install_playwright():
    try:
        from playwright.sync_api import sync_playwright
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def scrape_over_under_data(match_url: str, headless: bool = True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        
        # SETĂRI SPECIFICE ROMÂNIA
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ro-RO',
            timezone_id='Europe/Bucharest',
            # Adaugă headere ca să pară că e din România
            extra_http_headers={
                'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
                'X-Forwarded-For': '79.112.1.1'  # IP din România
            }
        )
        
        page = context.new_page()
        
        # Setează cookie pentru România înainte de navigare
        page.add_init_script("""
            Object.defineProperty(navigator, 'language', {
                get: function() { return 'ro-RO'; }
            });
            Object.defineProperty(navigator, 'languages', {
                get: function() { return ['ro-RO', 'ro', 'en-US', 'en']; }
            });
        """)
        
        page.goto(match_url, timeout=60000)
        time.sleep(5)
        
        if "#over-under" not in page.url:
            try:
                over_under_tab = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
                if over_under_tab.count() > 0:
                    over_under_tab.first.click()
                    time.sleep(5)
            except:
                pass
        
        # VERIFICĂ CE VEDEM
        page_content = page.content()
        print("🔍 VERIFIC CONTENTUL...")
        
        if "Betano" in page_content:
            print("✅ BETANO GĂSIT!")
        else:
            print("❌ BETANO NU E ÎN PAGINĂ")
            
        if "1." in page_content or "2." in page_content:
            print("✅ COTE DECIMALE")
        else:
            print("❌ COTE AMERICANE")
        
        # SCROLL
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        # EXTRAGE ORICE DATE GĂSIM
        scraped_data = []
        rows = page.locator('[data-testid="over-under-collapsed-row"]')
        
        print(f"📊 LINII GĂSITE: {rows.count()}")
        
        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                line_text = row.locator('[data-testid="over-under-collapsed-option-box"]').inner_text()
                over_odds = row.locator('[data-testid="odd-container-default"]:nth-child(1) p').inner_text()
                under_odds = row.locator('[data-testid="odd-container-default"]:nth-child(2) p').inner_text()
                
                scraped_data.append({
                    'total': line_text.replace("Over/Under", "").strip(),
                    'over': over_odds,
                    'under': under_odds
                })
                
                print(f"📝 Linia {i}: {line_text} | Over: {over_odds} | Under: {under_odds}")
                
            except Exception as e:
                print(f"⚠️ Eroare linia {i}: {e}")
                continue
        
        browser.close()
        
        if scraped_data:
            return {
                'url_final': page.url,
                'numar_linii': len(scraped_data),
                'date': scraped_data
            }
        return None
