import requests
from bs4 import BeautifulSoup
import re
import time
import json
from playwright.sync_api import sync_playwright

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING CU PLAYWRIGHT - Cel mai bun pentru JavaScript
    """
    
    results = {
        'Match': 'Scraping cu Playwright',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    def extract_betano_odds_playwright(page, url, market_type):
        """Extrage cotele Betano folosind Playwright"""
        try:
            print(f"  📡 Accesez: {url}")
            
            # Navighează la URL-ul direct cu linia
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Așteaptă să se încarce conținutul
            page.wait_for_timeout(3000)
            
            # Caută Betano în pagină
            betano_selector = "a[href*='betano']"
            betano_element = page.query_selector(betano_selector)
            
            if betano_element:
                print("  ✅ Betano găsit!")
                
                # Găsește rândul Betano
                betano_row = page.query_selector(f"{betano_selector} >> xpath=../..")
                
                if betano_row:
                    # Extrage cotele "line-through"
                    odds_selector = "p.odds-text.line-through"
                    odds_elements = betano_row.query_selector_all(odds_selector)
                    
                    if market_type == 'ou' and len(odds_elements) >= 2:
                        over_odd = odds_elements[0].inner_text().strip()
                        under_odd = odds_elements[1].inner_text().strip()
                        return over_odd, under_odd
                    
                    elif market_type == 'ah' and len(odds_elements) >= 2:
                        home_odd = odds_elements[0].inner_text().strip()
                        away_odd = odds_elements[1].inner_text().strip()
                        return home_odd, away_odd
            
            return 'N/A', 'N/A'
            
        except Exception as e:
            print(f"  ❌ Eroare extragere cote: {e}")
            return 'N/A', 'N/A'
    
    try:
        print("=== ÎNCEPE SCRAPING CU PLAYWRIGHT ===")
        
        with sync_playwright() as p:
            # Lansează browser-ul
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # OVER/UNDER
            print("🔍 Extrag linii Over/Under...")
            page.goto(ou_link, wait_until='networkidle', timeout=30000)
            
            # Așteaptă să se încarce conținutul
            page.wait_for_timeout(5000)
            
            # Caută toate liniile Over/Under
            ou_lines = []
            
            # Selector pentru liniile Over/Under
            line_selector = "p:has-text('Over/Under')"
            line_elements = page.query_selector_all(line_selector)
            
            print(f"📊 Elemente Over/Under găsite: {len(line_elements)}")
            
            # Extrage textul din primele 10 elemente
            unique_lines = []
            for i, element in enumerate(line_elements[:10]):
                try:
                    text = element.inner_text().strip()
                    print(f"  🔍 Text element {i+1}: {text}")
                    
                    match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        if line_val not in unique_lines:
                            unique_lines.append(line_val)
                            print(f"  📈 Linie găsită: +{line_val}")
                except Exception as e:
                    print(f"  ⚠️ Eroare element {i+1}: {e}")
                    continue
            
            # Procesează liniile unice
            for i, line_val in enumerate(unique_lines[:5]):
                try:
                    display_line = f"+{line_val}"
                    base_url = ou_link.split('#')[0]
                    direct_url = f"{base_url}#over-under;1;{line_val};0"
                    
                    print(f"  🎯 Procesez linia {i+1}: {display_line}")
                    
                    over_odd, under_odd = extract_betano_odds_playwright(page, direct_url, 'ou')
                    
                    ou_lines.append({
                        'Line': display_line,
                        'Over_Close': over_odd,
                        'Under_Close': under_odd,
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ⚠️ Eroare procesare linia {i+1}: {e}")
                    continue
            
            # ASIAN HANDICAP
            print("\n🔍 Extrag linii Asian Handicap...")
            page.goto(ah_link, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(5000)
            
            ah_lines = []
            
            ah_selector = "p:has-text('Asian Handicap')"
            ah_elements = page.query_selector_all(ah_selector)
            
            print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
            
            # Extrage liniile AH
            ah_unique_lines = []
            for i, element in enumerate(ah_elements[:10]):
                try:
                    text = element.inner_text().strip()
                    print(f"  🔍 Text AH {i+1}: {text}")
                    
                    match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                    if match:
                        line_val = match.group(1)
                        if line_val not in ah_unique_lines:
                            ah_unique_lines.append(line_val)
                            print(f"  📈 Linie AH găsită: {line_val}")
                except Exception as e:
                    print(f"  ⚠️ Eroare AH element {i+1}: {e}")
                    continue
            
            # Procesează liniile AH
            for i, line_val in enumerate(ah_unique_lines[:3]):
                try:
                    clean_val = line_val.replace('+', '').replace('-', '')
                    base_url = ah_link.split('#')[0]
                    direct_url = f"{base_url}#ah;1;{clean_val};0"
                    
                    print(f"  🎯 Procesez linia AH {i+1}: {line_val}")
                    
                    home_odd, away_odd = extract_betano_odds_playwright(page, direct_url, 'ah')
                    
                    ah_lines.append({
                        'Line': line_val,
                        'Home_Close': home_odd,
                        'Away_Close': away_odd,
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ⚠️ Eroare procesare AH {i+1}: {e}")
                    continue
            
            # Închide browser-ul
            browser.close()
            
            # Salvează rezultatele
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
            
            results['Debug'] = {
                'ou_lines_found': len(ou_lines),
                'ah_lines_found': len(ah_lines),
                'unique_ou_lines': unique_lines,
                'unique_ah_lines': ah_unique_lines,
                'strategy': 'Playwright - JavaScript rendering',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"✅ SCRAPING COMPLETAT: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
    
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    return results
