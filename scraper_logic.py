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
        
        # Testează dacă chromium funcționează
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

# Verifică și instalează la început
install_playwright()

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
            
            # Încearcă să dea click pe Over/Under folosind XPath-ul tău
            print("🖱️ Se încearcă click pe tab-ul Over/Under...")
            
            over_under_xpath = "/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[1]/div[1]/ul/li[3]/a"
            
            try:
                # Așteaptă elementul să fie disponibil
                page.wait_for_selector(f"xpath={over_under_xpath}", timeout=10000)
                
                # Dă click pe element
                page.click(f"xpath={over_under_xpath}")
                print("✅ Click realizat pe Over/Under!")
                
                # Așteaptă 5 secunde exact cum ai cerut
                print("⏳ Aștept 5 secunde...")
                time.sleep(5)
                
                # Capturează noul URL
                new_url = page.url
                print(f"🔄 URL nou după click: {new_url}")
                
                # Verifică dacă URL-ul s-a schimbat
                if new_url != initial_url:
                    print("✅ SUCCES: URL-ul s-a schimbat - Over/Under a funcționat!")
                else:
                    print("⚠️ ATENȚIE: URL-ul nu s-a schimbat - posibilă problemă")
                
                browser.close()
                return new_url
                
            except Exception as e:
                print(f"❌ Eroare la click: {e}")
                print("🔍 Se verifică HTML-ul paginii...")
                
                # Afisează HTML-ul pentru debugging
                html_content = page.content()
                print(f"📄 Primele 2000 de caractere din HTML:")
                print(html_content[:2000])
                
                browser.close()
                return None
                
    except Exception as e:
        print(f"❌ Eroare critică: {str(e)}")
        return None

# Test funcție
if __name__ == "__main__":
    test_url = "https://www.oddsportal.com/basketball/usa/nba/boston-celtics-los-angeles-clippers-OYHzgRy3/#home-away;1"
    result = click_over_under_and_get_url(test_url, headless=False)
    
    if result:
        print(f"🎉 FINAL - URL Over/Under: {result}")
    else:
        print("❌ Testul a eșuat")
