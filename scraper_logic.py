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
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-GB'
        )
        
        page = context.new_page()
        
        print(f"📄 Navighez la: {match_url}")
        page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        
        print(f"🔗 URL curent: {page.url}")
        
        # CLICK PE OVER/UNDER
        if "#over-under" not in page.url:
            print("🖱️ Caut tab-ul Over/Under...")
            try:
                page.wait_for_selector('[data-testid="navigation-inactive-tab"]', timeout=10000)
                over_under_tab = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
                
                if over_under_tab.count() > 0:
                    print("✅ Găsit Over/Under - dau click...")
                    over_under_tab.first.click()
                    time.sleep(5)
                    print(f"🔗 URL după click: {page.url}")
                else:
                    print("❌ Nu am găsit tab-ul Over/Under")
                    return None
            except Exception as e:
                print(f"❌ Eroare la click: {e}")
                return None
        
        # SCROLL
        print("📜 Derulez pagina...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        
        # EXTRAGERE DATE
        print("🔍 Extrag liniile...")
        scraped_data = []
        
        try:
            rows = page.locator('[data-testid="over-under-collapsed-row"]')
            row_count = rows.count()
            print(f"📊 Am găsit {row_count} linii")
            
            for i in range(row_count):
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
                    
        except Exception as e:
            print(f"❌ Eroare la extragere: {e}")
            return None
        
        browser.close()
        
        if scraped_data:
            print(f"🎉 EXTRAS {len(scraped_data)} LINII!")
            return {
                'url_final': page.url,
                'numar_linii': len(scraped_data),
                'date': scraped_data
            }
        else:
            print("❌ NU AM EXTRAS NICI O LINIE")
            return None
