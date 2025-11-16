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

def debug_complete_extraction(match_url: str, headless: bool = True):
    """
    DEBUG COMPLET: Verifică totul pas cu pas
    """
    print("🐛 DEBUG COMPLET - Începe...")
    
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
            
            # 1. Navigare
            print(f"🌐 1. Se încarcă: {match_url}")
            page.goto(match_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            print(f"   📄 Titlu: {page.title()}")
            print(f"   🔗 URL: {page.url}")
            
            # 2. Click pe Over/Under
            print("🖱️ 2. Se caută Over/Under tab...")
            inactive_over_under = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")')
            print(f"   🔍 Over/Under găsit: {inactive_over_under.count()} elemente")
            
            if inactive_over_under.count() > 0:
                inactive_over_under.first.click()
                print("   ✅ Click pe Over/Under!")
                time.sleep(5)
                print(f"   🔗 URL după click: {page.url}")
            else:
                print("   ❌ Over/Under negăsit!")
                browser.close()
                return {"error": "Over/Under negăsit"}
            
            # 3. Derulare
            print("🔄 3. Derulare...")
            for scroll_attempt in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            time.sleep(3)
            
            # 4. Verifică liniile
            print("📋 4. Verifică liniile...")
            all_lines = page.locator('[data-testid="over-under-collapsed-row"]')
            line_count = all_lines.count()
            print(f"   📊 Total linii: {line_count}")
            
            if line_count == 0:
                print("   ❌ Nici o linie găsită!")
                browser.close()
                return {"error": "Nici o linie găsită"}
            
            # 5. TEST: Prima linie
            print("\n🔍 5. TEST - Prima linie:")
            first_line = all_lines.first
            line_text = first_line.locator('[data-testid="over-under-collapsed-option-box"]').first.inner_text()
            print(f"   📝 Text linie: {line_text}")
            
            # 6. Click pe săgeată
            print("   🖱️ Se dă click pe săgeată...")
            arrow = first_line.locator('.bg-provider-arrow').first
            if arrow.is_visible():
                arrow.click()
                time.sleep(3)
                
                # 7. Verifică rândurile expandate
                print("   📊 7. Verifică rândurile expandate...")
                expanded_rows = page.locator('[data-testid="over-under-expanded-row"]')
                expanded_count = expanded_rows.count()
                print(f"      Rânduri expandate: {expanded_count}")
                
                if expanded_count == 0:
                    print("      ❌ Nici un rând expandat!")
                else:
                    # 8. Verifică TOȚI bookmakerii
                    print("      📋 8. Lista bookmakeri:")
                    all_bookmakers = page.locator('[data-testid="outrights-expanded-bookmaker-name"]')
                    bookmaker_count = all_bookmakers.count()
                    print(f"         Total bookmakeri: {bookmaker_count}")
                    
                    betano_found = False
                    for i in range(bookmaker_count):
                        try:
                            bookmaker = all_bookmakers.nth(i)
                            name = bookmaker.inner_text().strip()
                            print(f"         Bookmaker {i+1}: {name}")
                            if 'Betano' in name:
                                betano_found = True
                                print(f"         ✅ BETANO GĂSIT la poziția {i+1}!")
                        except:
                            print(f"         Bookmaker {i+1}: EROARE la citire")
                    
                    if not betano_found:
                        print("         ❌ BETANO NU este în listă!")
                    
                    # 9. Verifică dacă există vreun bookmaker cu cote
                    print("      💰 9. Verifică cote bookmakeri:")
                    for i in range(min(3, bookmaker_count)):  # Primele 3
                        try:
                            bookmaker = all_bookmakers.nth(i)
                            bookmaker_name = bookmaker.inner_text().strip()
                            
                            # Găsește containerul părinte
                            bookmaker_row = bookmaker.locator('xpath=./ancestor::div[@data-testid="over-under-expanded-row"]').first
                            odds_containers = bookmaker_row.locator('[data-testid="odd-container"]')
                            
                            if odds_containers.count() >= 2:
                                over_text = odds_containers.nth(0).locator('.odds-text').first.inner_text().strip()
                                under_text = odds_containers.nth(1).locator('.odds-text').first.inner_text().strip()
                                print(f"         {bookmaker_name}: Over={over_text}, Under={under_text}")
                            else:
                                print(f"         {bookmaker_name}: Fără cote suficiente")
                                
                        except Exception as e:
                            print(f"         Eroare la bookmaker {i+1}: {e}")
                
                # Închide linia
                arrow.click()
                time.sleep(1)
            else:
                print("   ❌ Săgeată negăsită!")
            
            browser.close()
            
            return {
                "status": "DEBUG_COMPLET",
                "linii_gasite": line_count,
                "randuri_expandate": expanded_count if 'expanded_count' in locals() else 0,
                "bookmakeri_gasiti": bookmaker_count if 'bookmaker_count' in locals() else 0
            }
                
    except Exception as e:
        print(f"❌ Eroare debug: {str(e)}")
        import traceback
        print(f"🔍 Detalii eroare: {traceback.format_exc()}")
        return {"error": str(e)}
