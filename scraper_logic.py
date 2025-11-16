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
    print("🚀 START SCRAPING...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        print(f"📄 Navighez la: {match_url}")
        page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        
        # CLICK PE OVER/UNDER
        if "#over-under" not in page.url:
            print("🖱️ Caut tab-ul Over/Under...")
            page.wait_for_selector('[data-testid="navigation-inactive-tab"]', timeout=10000)
            over_under_tab = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if over_under_tab.count() > 0:
                print("✅ Găsit Over/Under - dau click...")
                over_under_tab.first.click()
                time.sleep(5)
        
        # SCROLL
        print("📜 Derulez pagina...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        
        # EXTRAG HTML-UL COMPLET
        print("🔍 Extrag HTML-ul...")
        html_content = page.content()
        
        # SALVEAZĂ HTML PENTRU DEBUG
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("💾 HTML salvat în debug_page.html")
        
        # CAUTĂ BETANO ÎN HTML
        if "Betano" in html_content:
            print("✅ BETANO GĂSIT ÎN HTML!")
            
            # Extrage toate liniile collapsed
            scraped_data = []
            rows = page.locator('[data-testid="over-under-collapsed-row"]')
            
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    
                    # TOTAL
                    total_text = row.locator('[data-testid="over-under-collapsed-option-box"]').inner_text()
                    if "Over/Under" in total_text:
                        total = total_text.replace("Over/Under", "").strip()
                    elif "O/U" in total_text:
                        total = total_text.replace("O/U", "").strip()
                    else:
                        total = total_text
                    
                    # COTE
                    over_odds = row.locator('[data-testid="odd-container-default"]:nth-child(1) p').inner_text()
                    under_odds = row.locator('[data-testid="odd-container-default"]:nth-child(2) p').inner_text()
                    
                    scraped_data.append({
                        'total': total,
                        'over': over_odds,
                        'under': under_odds
                    })
                    
                    print(f"✅ Linia {i+1}: {total} | Over: {over_odds} | Under: {under_odds}")
                    
                except Exception as e:
                    print(f"⚠️ Eroare la linia {i+1}: {e}")
                    continue
            
            browser.close()
            
            if scraped_data:
                return {
                    'url_final': page.url,
                    'numar_linii': len(scraped_data),
                    'date': scraped_data
                }
        
        print("❌ BETANO NU A FOST GĂSIT ÎN HTML")
        browser.close()
        return None
