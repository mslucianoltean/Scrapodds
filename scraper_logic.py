import requests
from bs4 import BeautifulSoup
import re
import time
import urllib3
import json

# Dezactivează avertismentele SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING REAL - Cu fix pentru formatul JSON Streamlit
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # STRUCTURA CORECTĂ PENTRU STREAMLIT
    results = {
        'Match': 'Scraping Real OddsPortal',
        'Over_Under_Lines': [],
        'Handicap_Lines': [],
        'Debug': {},
        'Error': None
    }
    
    def extract_betano_odds(url, market_type):
        """Extrage cotele Betano"""
        try:
            print(f"  📡 Accesez: {url}")
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
            
            if betano_row:
                print("  ✅ Betano găsit!")
                odds_elements = betano_row.find_all('p', class_='odds-text line-through')
                
                if market_type == 'ou' and len(odds_elements) >= 2:
                    return odds_elements[0].get_text(strip=True), odds_elements[1].get_text(strip=True)
                elif market_type == 'ah' and len(odds_elements) >= 2:
                    return odds_elements[0].get_text(strip=True), odds_elements[1].get_text(strip=True)
            
            return 'N/A', 'N/A'
            
        except Exception as e:
            print(f"  ❌ Eroare cote: {e}")
            return 'N/A', 'N/A'
    
    try:
        print("=== ÎNCEPE SCRAPING REAL ===")
        
        # OVER/UNDER
        print("🔍 Extrag linii Over/Under...")
        response_ou = requests.get(ou_link, headers=headers, timeout=15, verify=False)
        soup_ou = BeautifulSoup(response_ou.content, 'html.parser')
        
        ou_lines = []
        
        # Caută liniile Over/Under
        ou_elements = soup_ou.find_all('p', string=re.compile(r'Over/Under'))
        
        if not ou_elements:
            # Încearcă alt selector
            all_elements = soup_ou.find_all(string=re.compile(r'Over/Under'))
            ou_elements = [elem for elem in all_elements if 'Over/Under' in str(elem)]
        
        print(f"📊 Elemente Over/Under găsite: {len(ou_elements)}")
        
        # Extrage liniile unice
        unique_lines = []
        for element in ou_elements[:15]:
            try:
                text = element if isinstance(element, str) else element.get_text()
                match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                if match:
                    line_val = match.group(1)
                    if line_val not in unique_lines:
                        unique_lines.append(line_val)
                        print(f"  📈 Linie găsită: +{line_val}")
            except:
                continue
        
        # Procesează liniile
        for i, line_val in enumerate(unique_lines[:5]):
            try:
                display_line = f"+{line_val}"
                base_url = ou_link.split('#')[0]
                direct_url = f"{base_url}#over-under;1;{line_val};0"
                
                print(f"  🎯 Procesez: {display_line}")
                
                over_odd, under_odd = extract_betano_odds(direct_url, 'ou')
                
                ou_lines.append({
                    'Line': display_line,
                    'Over_Close': over_odd,
                    'Under_Close': under_odd,
                    'Bookmaker': 'Betano.ro',
                    'Direct_URL': direct_url
                })
                
                time.sleep(1)
                
            except Exception as e:
                print(f"  ⚠️ Eroare linia {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP
        print("\n🔍 Extrag linii Asian Handicap...")
        response_ah = requests.get(ah_link, headers=headers, timeout=15, verify=False)
        soup_ah = BeautifulSoup(response_ah.content, 'html.parser')
        
        ah_lines = []
        
        ah_elements = soup_ah.find_all('p', string=re.compile(r'Asian Handicap'))
        
        if not ah_elements:
            all_elements = soup_ah.find_all(string=re.compile(r'Asian Handicap'))
            ah_elements = [elem for elem in all_elements if 'Asian Handicap' in str(elem)]
        
        print(f"📊 Elemente Asian Handicap găsite: {len(ah_elements)}")
        
        # Extrage liniile AH unice
        ah_unique_lines = []
        for element in ah_elements[:15]:
            try:
                text = element if isinstance(element, str) else element.get_text()
                match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                if match:
                    line_val = match.group(1)
                    if line_val not in ah_unique_lines:
                        ah_unique_lines.append(line_val)
                        print(f"  📈 Linie AH găsită: {line_val}")
            except:
                continue
        
        # Procesează liniile AH
        for i, line_val in enumerate(ah_unique_lines[:3]):
            try:
                clean_val = line_val.replace('+', '').replace('-', '')
                base_url = ah_link.split('#')[0]
                direct_url = f"{base_url}#ah;1;{clean_val};0"
                
                print(f"  🎯 Procesez AH: {line_val}")
                
                home_odd, away_odd = extract_betano_odds(direct_url, 'ah')
                
                ah_lines.append({
                    'Line': line_val,
                    'Home_Close': home_odd,
                    'Away_Close': away_odd,
                    'Bookmaker': 'Betano.ro',
                    'Direct_URL': direct_url
                })
                
                time.sleep(1)
                
            except Exception as e:
                print(f"  ⚠️ Eroare AH {i+1}: {e}")
                continue
        
        # SALVARE REZULTATE - FORMAT CORECT
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'total_ou_elements': len(ou_elements),
            'total_ah_elements': len(ah_elements),
            'unique_ou_lines': unique_lines,
            'unique_ah_lines': ah_unique_lines,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ FINAL: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE: {e}")
    
    # VERIFICĂ DACA E VALID JSON
    try:
        json.dumps(results)  # Testează dacă e JSON valid
        return results
    except Exception as e:
        print(f"❌ JSON INVALID: {e}")
        # Returnează structură safe
        return {
            'Match': 'Scraping - Eroare JSON',
            'Over_Under_Lines': [],
            'Handicap_Lines': [],
            'Debug': {'error': 'Invalid JSON structure'},
            'Error': 'Format invalid'
        }
