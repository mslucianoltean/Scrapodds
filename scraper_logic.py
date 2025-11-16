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

def extract_betano_with_link(match_url: str, headless: bool = True):
    """
    COMPLET: Home/Away → Click Over/Under → Click săgeată → Găsește Betano după LINK → Extrage cotele
    """
    print("🎯 PROCES COMPLET CU LEGĂTURĂ BETANO-COTE")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process'],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 2000},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # 1. PORNEȘTE DE LA HOME/AWAY
            print(f"📍 1. Se încarcă de la Home/Away: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            print(f"   🔗 URL start: {page.url}")
            
            # 2. CLICK PE OVER/UNDER TAB
            print("📍 2. Click pe Over/Under tab...")
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                print("   ✅ Click Over/Under!")
                time.sleep(5)
                print(f"   🔗 URL după Over/Under: {page.url}")
                
                # 3. DERULEAZĂ
                print("📍 3. Derulare...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                
                # 4. GĂSEȘTE LINIILE
                all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
                line_count = all_lines.count()
                print(f"   📊 Linii găsite: {line_count}")
                
                if line_count == 0:
                    print("   ❌ Nicio linie!")
                    browser.close()
                    return None
                
                # 5. CLICK PE SĂGEATA PRIMEI LINII
                print("📍 4. Click pe săgeata primei linii...")
                first_line = all_lines.first
                line_text = first_line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
                print(f"   📝 Linia: {line_text}")
                
                arrow = first_line.locator('.bg-provider-arrow').first
                if arrow.is_visible():
                    arrow.click()
                    print("   ✅ Click săgeată!")
                    time.sleep(3)
                    
                    # 6. CAUTĂ BETANO DUPĂ LINK ȘI EXTRAGE COTELE DIN ACELAȘI RÂND
                    print("📍 5. Căutare Betano după LINK și extracție cote...")
                    expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
                    expanded_count = expanded_rows.count()
                    print(f"   📊 Rânduri expandate: {expanded_count}")
                    
                    if expanded_count > 0:
                        for i in range(expanded_count):
                            row = expanded_rows.nth(i)
                            
                            # CAUTĂ BETANO DUPĂ LINK (href care conține "betano")
                            betano_link = row.locator('a[href*="betano"]').first
                            if betano_link.count() > 0 and betano_link.is_visible():
                                print("   ✅ BETANO GĂSIT după LINK!")
                                
                                # EXTRAGE COTELE DIN ACELAȘI RÂND
                                odds_containers = row.locator('[data-testid="odd-container"]')
                                print(f"   📊 Containere cote în rândul Betano: {odds_containers.count()}")
                                
                                if odds_containers.count() >= 2:
                                    over_text = odds_containers.nth(0).locator('.odds-text').first.inner_text().strip()
                                    under_text = odds_containers.nth(1).locator('.odds-text').first.inner_text().strip()
                                    
                                    print(f"   🎯 Cote Betano: Over={over_text}, Under={under_text}")
                                    
                                    # Închide linia
                                    arrow.click()
                                    time.sleep(1)
                                    
                                    browser.close()
                                    return [{
                                        'line': line_text,
                                        'over_closing': float(over_text),
                                        'under_closing': float(under_text)
                                    }]
                                else:
                                    print("   ❌ Nu sunt suficiente containere de cote")
                        
                        print("   ❌ Betano negăsit în rândurile expandate")
                    else:
                        print("   ❌ Nicio linie expandată")
                    
                    # Închide linia
                    arrow.click()
                    time.sleep(1)
                else:
                    print("   ❌ Săgeată negăsită")
            else:
                print("❌ Over/Under tab negăsit")
            
            browser.close()
            return None
                
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        import traceback
        print(f"🔍 Detalii: {traceback.format_exc()}")
        return None
