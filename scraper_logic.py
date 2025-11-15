import requests
from bs4 import BeautifulSoup
import re
import time
import urllib3

# Dezactivează avertismentele SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING REAL - Cu fix pentru problemele SSL
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    results = {
        'Match': 'Scraping Real OddsPortal',
        'Over_Under_Lines': [],
        'Handicap_Lines': []
    }
    
    def extract_betano_odds(url, market_type):
        """Extrage cotele Betano - cu fix SSL"""
        try:
            print(f"  📡 Accesez: {url}")
            
            # FOLOSEȘTE verify=False pentru probleme SSL
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Găsește Betano
            betano_row = None
            betano_links = soup.find_all('a', href=re.compile(r'betano', re.IGNORECASE))
            
            for link in betano_links:
                parent_tr = link.find_parent('tr')
                if parent_tr:
                    betano_row = parent_tr
                    break
            
            if not betano_row:
                # Încercă altă metodă
                all_rows = soup.find_all('tr')
                for row in all_rows:
                    if row.text and 'betano' in row.text.lower():
                        betano_row = row
                        break
            
            if betano_row:
                print("  ✅ Betano găsit!")
                odds_elements = betano_row.find_all('p', class_='odds-text line-through')
                
                if market_type == 'ou' and len(odds_elements) >= 2:
                    return odds_elements[0].get_text(strip=True), odds_elements[1].get_text(strip=True)
                elif market_type == 'ah' and len(odds_elements) >= 2:
                    return odds_elements[0].get_text(strip=True), odds_elements[1].get_text(strip=True)
            
            return 'N/A', 'N/A'
            
        except Exception as e:
            print(f"  ❌ Eroare extragere cote: {e}")
            return 'N/A', 'N/A'
    
    try:
        print("=== ÎNCEPE SCRAPING REAL ===")
        
        # OVER/UNDER - cu verificare SSL dezactivată
        print("🔍 Extrag linii Over/Under...")
        response_ou = requests.get(ou_link, headers=headers, timeout=15, verify=False)
        soup_ou = BeautifulSoup(response_ou.content, 'html.parser')
        
        ou_lines = []
        
        # Caută liniile Over/Under în mai multe moduri
        ou_elements = soup_ou.find_all('p', string=re.compile(r'Over/Under'))
        
        # Dacă nu găsește, încearcă alt selector
        if not ou_elements:
            ou_elements = soup_ou.find_all(string=re.compile(r'Over/Under'))
        
        print(f"📊 Elemente Over/Under găsite: {len(ou_elements)}")
        
        # Extrage primele 5 linii pentru test
        extracted_lines = []
        for element in ou_elements[:10]:
            text = element if isinstance(element, str) else element.get_text()
            match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
            if match:
                line_val = match.group(1)
                if line_val not in [l['Line'].replace('+', '') for l in extracted_lines]:
                    extracted_lines.append({
                        'Line': f"+{line_val}",
                        'Value': line_val
                    })
        
        print(f"📈 Linii unice extrase: {len(extracted_lines)}")
        
        # Procesează fiecare linie
        for i, line_data in enumerate(extracted_lines[:5]):  # Primele 5 pentru test
            try:
                line_val = line_data['Value']
                display_line = line_data['Line']
                
                # Construiește URL
                base_url = ou_link.split('#')[0]
                direct_url = f"{base_url}#over-under;1;{line_val};0"
                
                print(f"  🎯 Procesez linia {i+1}: {display_line}")
                
                # Extrage cotele Betano
                over_odd, under_odd = extract_betano_odds(direct_url, 'ou')
                
                ou_lines.append({
                    'Line': display_line,
                    'Over_Close': over_odd,
                    'Under_Close': under_odd,
                    'Bookmaker': 'Betano.ro',
                    'Direct_URL': direct_url
                })
                
                time.sleep(2)  # Pauză mai mare pentru cloud
                
            except Exception as e:
                print(f"  ⚠️ Eroare procesare linia {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP - același principiu
        print("\n🔍 Extrag linii Asian Handicap...")
        response_ah = requests.get(ah_link, headers=headers, timeout=15, verify=False)
        soup_ah = BeautifulSoup(response_ah.content, 'html.parser')
        
        ah_lines = []
        
        ah_elements = soup_ah.find_all('p', string=re.compile(r'Asian Handicap'))
        if not ah_elements:
            ah_elements = soup_ah.find_all(string=re.compile(r'Asian Handicap'))
        
        print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
        
        # Extrage primele 3 linii AH pentru test
        ah_extracted = []
        for element in ah_elements[:8]:
            text = element if isinstance(element, str) else element.get_text()
            match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
            if match:
                line_val = match.group(1)
                clean_val = line_val.replace('+', '').replace('-', '')
                if clean_val not in [l['Value'] for l in ah_extracted]:
                    ah_extracted.append({
                        'Line': line_val,
                        'Value': clean_val
                    })
        
        for i, line_data in enumerate(ah_extracted[:3]):
            try:
                line_val = line_data['Line']
                clean_val = line_data['Value']
                
                base_url = ah_link.split('#')[0]
                direct_url = f"{base_url}#ah;1;{clean_val};0"
                
                print(f"  🎯 Procesez linia AH {i+1}: {line_val}")
                
                home_odd, away_odd = extract_betano_odds(direct_url, 'ah')
                
                ah_lines.append({
                    'Line': line_val,
                    'Home_Close': home_odd,
                    'Away_Close': away_odd,
                    'Bookmaker': 'Betano.ro',
                    'Direct_URL': direct_url
                })
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ⚠️ Eroare procesare AH {i+1}: {e}")
                continue
        
        # Salvează rezultatele
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'strategy': 'Scraping cu fix SSL',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLETAT: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE CRITICĂ: {e}")
    
    return results
