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

def extract_betano_closing_odds(match_url: str, headless: bool = True):
    """
    Extrage cotele de CLOSING de la Betano pentru toate liniile
    """
    print("🌐 Se extrag cotele de CLOSING de la Betano...")
    
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
            
            # Derulează pentru toate liniile
            print("🔄 Se derulează pentru toate liniile...")
            for scroll_attempt in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            time.sleep(3)
            
            # Găsește toate liniile
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            print(f"📊 Total linii: {line_count}")
            
            results = []
            
            # Extrage cotele de closing pentru fiecare linie
            for i in range(line_count):
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
                        
                        # Caută rândul Betano în rândurile expandate
                        betano_odds = find_betano_odds_in_expanded_rows(page)
                        
                        if betano_odds:
                            print(f"   ✅ Betano - Over: {betano_odds['over']}, Under: {betano_odds['under']}")
                            results.append({
                                'line': line_text,
                                'over_closing': betano_odds['over'],
                                'under_closing': betano_odds['under']
                            })
                        else:
                            print(f"   ❌ Betano negăsit în linia deschisă")
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
            
            # Numără câte linii au cote valide
            valid_results = [r for r in results if r['over_closing'] != 'N/A']
            print(f"\n🎯 EXTRACȚIE COMPLETĂ: {len(valid_results)} linii cu cote Betano")
            return valid_results
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return None

def find_betano_odds_in_expanded_rows(page):
    """
    Caută Betano în rândurile expandate și extrage cotele
    """
    try:
        # Găsește toate rândurile expandate
        expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
        
        for i in range(expanded_rows.count()):
            row = expanded_rows.nth(i)
            
            # Verifică dacă acest rând conține Betano
            betano_name = row.locator('[data-testid="outrights-expanded-bookmaker-name"]')
            if betano_name.count() > 0:
                bookmaker_text = betano_name.first.inner_text().strip()
                if 'Betano' in bookmaker_text:
                    print(f"   ✅ Betano găsit în rândul expandat {i+1}")
                    
                    # Extrage cotele din acest rând
                    odds_containers = row.locator('[data-testid="odd-container"]')
                    
                    if odds_containers.count() >= 2:
                        # Over closing - primul container
                        over_text = odds_containers.nth(0).locator('.odds-text').first.inner_text().strip()
                        
                        # Under closing - al doilea container  
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
        
        print("   ❌ Betano nu a fost găsit în niciun rând expandat")
        return None
        
    except Exception as e:
        print(f"⚠️ Eroare căutare Betano: {e}")
        return None
