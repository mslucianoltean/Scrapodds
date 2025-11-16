from playwright.sync_api import sync_playwright
import time

def debug_container_content(match_url: str, headless: bool = True):
    """
    DEBUG: Afișează EXACT ce este în containerul expandat
    """
    print("🐛 DEBUG - Se afișează conținutul containerului expandat...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1920, 'height': 2000})
            page = context.new_page()
            
            # Procesul complet
            page.goto(match_url, wait_until='domcontentloaded')
            time.sleep(3)
            
            # Click Over/Under
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                time.sleep(5)
                
            # Derulează
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            # Click pe prima săgeată
            first_line = page.locator('[data-testid="over-under-collapsed-row"]').first
            arrow = first_line.locator('.bg-provider-arrow').first
            if arrow.is_visible():
                arrow.click()
                time.sleep(3)
                
                # DEBUG: Afișează TOT din containerul expandat
                expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
                print(f"📊 RÂNDURI EXPANDATE: {expanded_rows.count()}")
                
                for i in range(expanded_rows.count()):
                    row = expanded_rows.nth(i)
                    print(f"\n🔍 RÂNDUL {i+1}:")
                    print("HTML COMPLET:")
                    print(row.inner_html()[:1000])  # Primele 1000 caractere
                    
                    # Verifică ce link-uri sunt
                    all_links = row.locator('a')
                    print(f"🔗 LINK-URI: {all_links.count()}")
                    for j in range(all_links.count()):
                        link = all_links.nth(j)
                        href = link.get_attribute('href')
                        print(f"   Link {j+1}: {href}")
                    
                    # Verifică ce containere de cote sunt
                    odds_containers = row.locator('[data-testid="odd-container"]')
                    print(f"💰 CONTAINERE COTE: {odds_containers.count()}")
                    
                arrow.click()
                
            browser.close()
            return {"status": "DEBUG_COMPLETAT"}
                
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        return {"error": str(e)}
