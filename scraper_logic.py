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
        
        # FORȚEAZĂ SETĂRI PENTRU ROMÂNIA
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ro-RO',  # ROMÂNIA
            geolocation={'latitude': 44.4268, 'longitude': 26.1025},  # BUCUREȘTI
            permissions=['geolocation'],
            timezone_id='Europe/Bucharest'
        )
        
        page = context.new_page()
        
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
        
        # SCROLL
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        # VERIFICĂ DACA VEDEM COTE DECIMALE
        page_content = page.content()
        if "1." in page_content or "2." in page_content:  # Cote decimale
            print("✅ VĂD COTE DECIMALE (ROMÂNIA)")
        else:
            print("❌ VĂD COTE AMERICANE (ALTĂ ȚARĂ)")
        
        # EXTRAGE DATELE
        scraped_data = []
        rows = page.locator('[data-testid="over-under-collapsed-row"]')
        
        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                line_text = row.locator('[data-testid="over-under-collapsed-option-box"]').inner_text()
                over_odds = row.locator('[data-testid="odd-container-default"]:nth-child(1) p').inner_text()
                under_odds = row.locator('[data-testid="odd-container-default"]:nth-child(2) p').inner_text()
                
                # VERIFICĂ DACA SUNT COTE DECIMALE
                if "." in over_odds and "." in under_odds:
                    scraped_data.append({
                        'total': line_text.replace("Over/Under", "").strip(),
                        'over': over_odds,
                        'under': under_odds
                    })
            except:
                continue
        
        browser.close()
        
        if scraped_data:
            return {
                'url_final': page.url,
                'numar_linii': len(scraped_data),
                'date': scraped_data
            }
        return None
