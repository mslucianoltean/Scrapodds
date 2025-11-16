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
        page = browser.new_page()
        
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
        
        # EXPAND TOATE LINIILE ȘI EXTRAGE BETANO
        scraped_data = []
        rows = page.locator('[data-testid="over-under-collapsed-row"]')
        
        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                
                # TOTAL
                total_text = row.locator('[data-testid="over-under-collapsed-option-box"]').inner_text()
                if "Over/Under" in total_text:
                    total = total_text.replace("Over/Under", "").strip()
                else:
                    total = total_text
                
                # CLICK PE SĂGEATĂ SĂ EXPANDEZE
                expand_arrow = row.locator('.bg-provider-arrow')
                if expand_arrow.count() > 0:
                    expand_arrow.click()
                    time.sleep(1)
                    
                    # EXTRAGE BOOKMAKERII EXPANDAȚI
                    expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
                    
                    for j in range(expanded_rows.count()):
                        try:
                            expanded_row = expanded_rows.nth(j)
                            
                            # VERIFICĂ DACA E BETANO
                            bookmaker_name = expanded_row.locator('[data-testid="outrights-expanded-bookmaker-name"]').inner_text()
                            
                            if "Betano" in bookmaker_name:
                                # EXTRAGE COTELE DECIMALE
                                over_odds = expanded_row.locator('[data-testid="odd-container"]:nth-child(3) .odds-text').inner_text()
                                under_odds = expanded_row.locator('[data-testid="odd-container"]:nth-child(4) .odds-text').inner_text()
                                
                                scraped_data.append({
                                    'bookmaker': bookmaker_name,
                                    'total': total,
                                    'over': over_odds,
                                    'under': under_odds
                                })
                        except:
                            continue
            except:
                continue
        
        browser.close()
        
        if scraped_data:
            return {
                'url_final': page.url,
                'numar_bookmakeri': len(scraped_data),
                'date': scraped_data
            }
        return None
