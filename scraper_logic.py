
def scrape_from_page_source(ou_link, ah_link):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import os
    import time
    import re
    import json
    
    results = {'Match': 'Scraping din page_source'}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("=== SCRAPING DIN PAGE_SOURCE ===")
        
        # ----------------------------------------------------
        # OVER/UNDER
        # ----------------------------------------------------
        print("=== OVER/UNDER ===")
        driver.get(ou_link)
        time.sleep(8)  # Așteaptă mai mult pentru încărcare completă
        
        # Salvează page_source pentru analiză
        ou_html = driver.page_source
        print(f"Lungime HTML OU: {len(ou_html)} caractere")
        
        # Caută Betano și cotele direct în HTML
        ou_lines = extract_data_from_html(ou_html, "Over/Under")
        results['Over_Under_Lines'] = ou_lines
        
        # ----------------------------------------------------
        # ASIAN HANDICAP
        # ----------------------------------------------------
        print("=== ASIAN HANDICAP ===")
        driver.get(ah_link)
        time.sleep(8)
        
        ah_html = driver.page_source
        print(f"Lungime HTML AH: {len(ah_html)} caractere")
        
        ah_lines = extract_data_from_html(ah_html, "Asian Handicap")
        results['Handicap_Lines'] = ah_lines
        
        # DEBUG: Verifică ce a găsit
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'ou_html_sample': ou_html[:500] if ou_html else 'N/A',
            'betano_in_ou': 'Betano.ro' in ou_html
        }
        
    except Exception as e:
        results['Error'] = f"Eroare: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
    return results

def extract_data_from_html(html, market_type):
    """Extrage datele direct din HTML"""
    lines = []
    
    print(f"Analiză HTML pentru {market_type}...")
    
    # Verifică dacă Betano există în HTML
    if 'Betano.ro' not in html:
        print(f"✗ Betano.ro NU este în HTML pentru {market_type}")
        return lines
    
    print(f"✓ Betano.ro este în HTML pentru {market_type}")
    
    # Caută structuri cu Betano și cote
    # Pattern 1: Betano cu cote în același context
    betano_patterns = [
        r'Betano\.ro[^>]*>[\s\S]{0,500}?(\d+\.\d+)[\s\S]{0,100}?(\d+\.\d+)',
        r'odds-text["\']>(\d+\.\d+)<[^>]*>[\s\S]{0,300}?Betano\.ro',
        r'Betano\.ro[\s\S]{0,200}?odds-text["\']>(\d+\.\d+)<[\s\S]{0,200}?odds-text["\']>(\d+\.\d+)<'
    ]
    
    for pattern in betano_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"✓ Găsite {len(matches)} potriviri cu pattern: {pattern[:50]}...")
            for match in matches[:3]:  # Primele 3 potriviri
                if isinstance(match, tuple) and len(match) >= 2:
                    odds = [str(odd) for odd in match[:2]]
                    lines.append({
                        'Line': 'Extras din HTML',
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Close': odds[0],
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Close': odds[1],
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Source': 'HTML_Extraction'
                    })
                    print(f"  - Cote: {odds[0]}/{odds[1]}")
            break
    
    # Dacă nu găsim cu pattern, încercăm să extragem toate cotele și să le asociem cu Betano
    if not lines:
        print("Încerc extragere manuală...")
        # Extrage toate cotele odds-text
        all_odds = re.findall(r'odds-text["\']>(\d+\.\d+)<', html)
        print(f"Total cote găsite în HTML: {len(all_odds)}")
        
        # Extrage poziția Betano
        betano_positions = [m.start() for m in re.finditer('Betano\.ro', html)]
        print(f"Poziții Betano în HTML: {len(betano_positions)}")
        
        # Pentru fiecare Betano, caută cele mai apropiate cote
        for i, betano_pos in enumerate(betano_positions[:5]):
            # Caută cote în vecinătatea Betano
            context_start = max(0, betano_pos - 1000)
            context_end = min(len(html), betano_pos + 1000)
            context = html[context_start:context_end]
            
            # Extrage cote din context
            context_odds = re.findall(r'odds-text["\']>(\d+\.\d+)<', context)
            if len(context_odds) >= 2:
                lines.append({
                    'Line': f'Linie {i+1}',
                    f'{"Over" if market_type == "Over/Under" else "Home"}_Close': context_odds[0],
                    f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                    f'{"Under" if market_type == "Over/Under" else "Away"}_Close': context_odds[1],
                    f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                    'Bookmaker': 'Betano.ro',
                    'Source': 'Context_Extraction'
                })
                print(f"✓ Betano {i+1}: {context_odds[0]}/{context_odds[1]}")
    
    print(f"Total linii extrase pentru {market_type}: {len(lines)}")
    return lines

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_from_page_source(ou_link, ah_link)
