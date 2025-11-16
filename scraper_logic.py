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

def extract_betano_odds_by_logo(match_url: str, headless: bool = True):
    """
    Extrage cotele Betano căutând după LOGO (nu text)
    """
    print("🌐 Se extrag cotele Betano (căutare după LOGO)...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',
                    '--disable-web-security'
                ],
                timeout=30000
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 2000},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            page = context.new_page()
            
            # Navigare + click pe Over/Under
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # Click pe Over/Under
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                print("✅ Click pe Over/Under!")
                time.sleep(5)
            
            # Derulează
            print("🔄 Se derulează...")
            for scroll_attempt in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            time.sleep(3)
            
            # Găsește toate liniile
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            print(f"📊 Total linii: {line_count}")
            
            results = []
            
            # Extrage cotele pentru primele 3 linii (test)
            for i in range(min(3, line_count)):
                try:
                    line = all_lines.nth(i)
                    line_text = line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
                    print(f"\n🔍 Linia {i+1}: {line_text}")
                    
                    # Dă click pe săgeată
                    arrow = line.locator('.bg-provider-arrow').first
                    if arrow.is_visible():
                        print("   ✅ Săgeată găsită - se dă click...")
                        arrow.click()
                        time.sleep(3)
                        
                        # CAUTĂ BETANO DUPĂ LOGO
                        betano_odds = find_betano_by_logo(page)
                        
                        if betano_odds:
                            print(f"   ✅ BETANO GĂSIT (logo)! - Over: {betano_odds['over']}, Under: {betano_odds['under']}")
                            results.append({
                                'line': line_text,
                                'over_closing': betano_odds['over'],
                                'under_closing': betano_odds['under']
                            })
                        else:
                            print(f"   ❌ Betano negăsit (niciun logo)")
                            results.append({
                                'line': line_text,
                                'over_closing': 'N/A',
                                'under_closing': 'N/A'
                            })
                        
                        # Închide linia
                        arrow.click()
                        time.sleep(1)
                    else:
                        print(f"   ❌ Fără săgeată")
                        results.append({
                            'line': line_text,
                            'over_closing': 'N/A',
                            'under_closing': 'N/A'
                        })
                        
                except Exception as e:
                    print(f"⚠️ Eroare la linia {i+1}: {e}")
                    results.append({
                        'line': f"Linia {i+1} - EROARE",
                        'over_closing': 'N/A',
                        'under_closing': 'N/A'
                    })
                    continue
            
            browser.close()
            
            valid_results = [r for r in results if r['over_closing'] != 'N/A']
            print(f"\n🎯 REZULTAT: {len(valid_results)} linii cu Betano găsite")
            return valid_results
                
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
        import traceback
        print(f"🔍 Detalii: {traceback.format_exc()}")
        return None

def find_betano_by_logo(page):
    """
    Caută Betano după LOGO-ul său și extrage cotele
    """
    try:
        # CAUTĂ LOGO-UL BETANO
        betano_logo = page.locator('img[alt="Betano.ro"]').first
        
        if betano_logo.is_visible():
            print("   ✅ Logo Betano găsit!")
            
            # Navighează la containerul părinte care conține cotele
            betano_row = betano_logo.locator('xpath=./ancestor::div[@data-testid="over-under-expanded-row"]').first
            
            if betano_row.is_visible():
                # Extrage cotele
                odds_containers = betano_row.locator('[data-testid="odd-container"]')
                
                if odds_containers.count() >= 2:
                    over_text = odds_containers.nth(0).locator('.odds-text').first.inner_text().strip()
                    under_text = odds_containers.nth(1).locator('.odds-text').first.inner_text().strip()
                    
                    try:
                        over_odds = float(over_text)
                        under_odds = float(under_text)
                        
                        return {
                            'over': over_odds,
                            'under': under_odds
                        }
                    except ValueError:
                        print(f"   ⚠️ Cote invalide: Over='{over_text}', Under='{under_text}'")
                        return None
            else:
                print("   ❌ Container Betano negăsit")
        else:
            print("   ❌ Logo Betano negăsit")
        
        return None
        
    except Exception as e:
        print(f"⚠️ Eroare căutare logo: {e}")
        return None
