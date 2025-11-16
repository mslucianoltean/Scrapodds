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
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-GB'
        )
        
        page = context.new_page()
        
        page.goto(match_url, timeout=60000)
        time.sleep(3)
        
        if "#over-under" not in page.url.lower():
            page.wait_for_selector('ul.visible-links.odds-tabs', timeout=10000)
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                time.sleep(3)
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        scraped_data = []
        rows = page.locator('[data-testid="over-under-collapsed-row"]')
        
        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                
                handicap_element = row.locator('[data-testid="over-under-collapsed-option-box"] p')
                handicap_text = handicap_element.inner_text()
                
                if "Over/Under" in handicap_text:
                    total = handicap_text.replace("Over/Under", "").strip()
                elif "O/U" in handicap_text: 
                    total = handicap_text.replace("O/U", "").strip()
                else:
                    total = handicap_text.strip()
                
                over_odds = row.locator('[data-testid="odd-container-default"]:nth-child(1) p').inner_text()
                under_odds = row.locator('[data-testid="odd-container-default"]:nth-child(2) p').inner_text()
                
                scraped_data.append({
                    'total': total,
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
