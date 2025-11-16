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

def extract_first_bookmaker_odds(match_url: str, headless: bool = True):
    """
    Extrage cotele de la PRIMUL bookmaker (Betano) pentru toate liniile
    """
    print("🌐 Se extrag cotele de la PRIMUL bookmaker (Betano)...")
    
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
            
            # Navigare la orice URL (chiar dacă e cu over-under)
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            print(f"📄 Pagina încărcată: {page.title()}")
            print(f"🔗 URL curent: {page.url}")
            
            # DĂ CLICK PE OVER/UNDER INDIFERENT DE URL-UL CURENT
            print("🖱️ Se dă click FORȚAT pe tab-ul Over/Under...")
            
            # Încearcă mai multe metode pentru a găsi și da click pe Over/Under
            over_under_clicked = False
            
            # Metoda 1: Inactive tab
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                print("✅ Click pe Over/Under (inactive tab)!")
                over_under_clicked = True
                time.sleep(5)
            
            # Metoda 2: Dacă nu s-a găsit inactive, înseamnă că poate e deja activ
            if not over_under_clicked:
                active_over_under = page.locator('[data-testid="navigation-active-tab"]:has-text("Over/Under")')
                if active_over_under.count() > 0:
                    print("✅ Over/Under este deja activ!")
                    over_under_clicked = True
                else:
                    # Metoda 3: Încearcă cu selector simplu
                    simple_over_under = page.locator('text=Over/Under')
                    if simple_over_under.count() > 0:
                        simple_over_under.first.click()
                        print("✅ Click pe Over/Under (selector simplu)!")
                        over_under_clicked = True
                        time.sleep(5)
            
            if not over_under_clicked:
                print("❌ Nu s-a putut da click pe Over/Under")
                browser.close()
                return None
            
            print(f"🔗 URL după click: {page.url}")
            
            # Derulează pentru toate liniile
            print("🔄 Se derulează pentru toate liniile...")
            for scroll_attempt in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                print(f"   Derulare {scroll_attempt + 1}/3")
            
            time.sleep(3)
            
            # Găsește toate liniile
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            print(f"📊 Total linii găsite: {line_count}")
            
            if line_count == 0:
                print("❌ Nicio linie găsită după click pe Over/Under!")
                browser.close()
                return None
            
            results = []
            
            # Extrage cotele pentru fiecare linie
            for i in range(min(line_count, 5)):  # Testează doar primele 5 linii pentru început
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
                        
                        # DEBUG: Verifică dacă există rânduri expandate
                        expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
                        print(f"   📊 Rânduri expandate găsite: {expanded_rows.count()}")
                        
                        # IA PRIMELE COTE DIN PRIMUL RÂND (BETANO)
                        betano_odds = extract_first_row_odds(page)
                        
                        if betano_odds:
                            print(f"   ✅ Betano (primul) - Over: {betano_odds['over']}, Under: {betano_odds['under']}")
                            results.append({
                                'line': line_text,
                                'over_closing': betano_odds['over'],
                                'under_closing': betano_odds['under']
                            })
                        else:
                            print(f"   ❌ Nu s-au găsit cote în primul rând")
                            # DEBUG: Verifică HTML-ul
                            page_html = page.content()
                            if 'Betano' in page_html:
                                print("   ℹ️ Betano este în HTML dar nu s-au putut extrage cotele")
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

def extract_first_row_odds(page):
    """
    Extrage cotele din PRIMUL rând expandat (Betano)
    """
    try:
        # Găsește PRIMUL rând expandat
        first_expanded_row = page.locator('[data-testid="over-under-expanded-row"]').first
        
        if first_expanded_row.count() > 0:
            print("   ✅ Rând expandat găsit!")
            
            # Extrage cotele din primul rând
            odds_containers = first_expanded_row.locator('[data-testid="odd-container"]')
            print(f"   📊 Containere de cote găsite: {odds_containers.count()}")
            
            if odds_containers.count() >= 2:
                # Over - primul container
                over_text = odds_containers.nth(0).locator('.odds-text').first.inner_text().strip()
                
                # Under - al doilea container  
                under_text = odds_containers.nth(1).locator('.odds-text').first.inner_text().strip()
                
                print(f"   📝 Cote brute: Over='{over_text}', Under='{under_text}'")
                
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
                print(f"   ❌ Nu sunt suficiente containere de cote")
        else:
            print("   ❌ Niciun rând expandat găsit")
        
        return None
        
    except Exception as e:
        print(f"⚠️ Eroare extragere cote: {e}")
        return None
