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

def click_over_under_and_get_url(match_url: str, headless: bool = True):
    """
    Dă click pe tab-ul Over/Under și returnează noul URL
    """
    print("🌐 Se lansează browser-ul...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Navigare la pagina initiala
            print(f"🌐 Se încarcă pagina: {match_url}")
            page.goto(match_url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
            
            # Afiseaza URL-ul initial
            initial_url = page.url
            print(f"📄 URL initial: {initial_url}")
            print(f"📄 Titlul paginii: {page.title()}")
            
            # VERIFICĂ dacă suntem deja pe Over/Under
            if "#over-under" in initial_url.lower():
                print("✅ DEJA suntem pe pagina Over/Under!")
                browser.close()
                return initial_url
            
            print("🖱️ Se încearcă click pe tab-ul Over/Under...")
            
            # Încearcă mai mulți selectori pentru Over/Under
            selectors = [
                "//div[text()='Over/Under']",  # XPath simplu
                "div:has-text('Over/Under')",  # CSS Selector
                "text=Over/Under",             # Text selector
                '[data-testid="navigation-inactive-tab"]:has-text("Over/Under")'  # TestID + text
            ]
            
            for selector in selectors:
                try:
                    print(f"🔍 Încerc selector: {selector}")
                    
                    if selector.startswith("//"):
                        # XPath
                        element = page.locator(f"xpath={selector}")
                    else:
                        # CSS/Text selector
                        element = page.locator(selector)
                    
                    if element.is_visible():
                        print(f"✅ Element găsit cu selector: {selector}")
                        
                        # Dă click pe element
                        element.click()
                        print("✅ Click realizat pe Over/Under!")
                        
                        # Așteaptă 5 secunde
                        print("⏳ Aștept 5 secunde...")
                        time.sleep(5)
                        
                        # Capturează noul URL
                        new_url = page.url
                        print(f"🔄 URL nou după click: {new_url}")
                        
                        browser.close()
                        return new_url
                        
                except Exception as e:
                    print(f"❌ Eroare cu selector {selector}: {e}")
                    continue
            
            # Dacă niciun selector nu a funcționat, afișează HTML pentru debugging
            print("❌ Niciun selector nu a funcționat. Se verifică HTML-ul...")
            html_content = page.content()
            print("📄 Fragment HTML cu tab-uri:")
            
            # Găsește și afișează doar partea cu tab-urile
            if '<ul class="visible-links odds-tabs' in html_content:
                start = html_content.find('<ul class="visible-links odds-tabs')
                end = html_content.find('</ul>', start) + 5
                tabs_html = html_content[start:end]
                print(tabs_html)
            else:
                print(html_content[:2000])
            
            browser.close()
            return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        return None
