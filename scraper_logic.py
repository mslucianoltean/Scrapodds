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
        
        # EXPAND TOATE LINIILE
        print("🔓 Expand toate liniile...")
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
                    
                    # CLICK PE SĂGEATA DE EXPAND
                    expand_arrow = row.locator('.bg-provider-arrow')
                    if expand_arrow.count() > 0:
                        expand_arrow.click()
                        time.sleep(1)
                        
                        # EXTRAGE BOOKMAKERII EXPANDAȚI
                        expanded_rows = page.locator(f'[data-testid="over-under-expanded-row"]:nth-of-type({i+1})')
                        
                        for j in range(expanded_rows.count()):
                            try:
                                expanded_row = expanded_rows.nth(j)
                                
                                # BOOKMAKER
                                bookmaker_name = expanded_row.locator('[data-testid="outrights-expanded-bookmaker-name"]').inner_text()
                                
                                # COTE
                                over_odds = expanded_row.locator('[data-testid="odd-container"]:nth-child(3) .odds-text').inner_text()
                                under_odds = expanded_row.locator('[data-testid="odd-container"]:nth-child(4) .odds-text').inner_text()
                                
                                scraped_data.append({
                                    'bookmaker': bookmaker_name,
                                    'total': total,
                                    'over': over_odds,
                                    'under': under_odds
                                })
                                
                                print(f"✅ {bookmaker_name}: {total} | Over: {over_odds} | Under: {under_odds}")
                                
                            except Exception as e:
                                print(f"⚠️ Eroare la bookmaker {j+1}: {e}")
                                continue
                    
                except Exception as e:
                    print(f"⚠️ Eroare la linia {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Eroare la extragere: {e}")
            return None
        
        browser.close()
        
        if scraped_data:
            print(f"🎉 EXTRAS {len(scraped_data)} BOOKMAKERI!")
            return {
                'url_final': page.url,
                'numar_bookmakeri': len(scraped_data),
                'date': scraped_data
            }
        else:
            print("❌ NU AM EXTRAS NICI UN BOOKMAKER")
            return None
