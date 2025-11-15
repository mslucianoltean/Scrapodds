import requests
from bs4 import BeautifulSoup
import re
import json
import time

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):  # NUMELE ORIGINAL!
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    results = {
        'Match': 'Scraping complet OddsPortal',
        'Over_Under_Lines': [],
        'Handicap_Lines': []
    }
    
    def extract_betano_odds_from_url(url, market_type='ou'):
        """Extrage cotele Betano dintr-un URL direct"""
        try:
            print(f"  Accesez URL pentru cote: {url}")
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Găsim rândul Betano
            betano_row = None
            betano_links = soup.find_all('a', href=re.compile(r'betano', re.IGNORECASE))
            for link in betano_links:
                parent_tr = link.find_parent('tr')
                if parent_tr:
                    betano_row = parent_tr
                    break
            
            if not betano_row:
                all_rows = soup.find_all('tr')
                for row in all_rows:
                    if 'betano' in row.text.lower():
                        betano_row = row
                        break
            
            if betano_row:
                print(f"  ✅ Rand Betano gasit!")
                odds_elements = betano_row.find_all('p', class_='odds-text line-through')
                
                if market_type == 'ou':
                    over_close = odds_elements[0].get_text(strip=True) if len(odds_elements) > 0 else 'N/A'
                    under_close = odds_elements[1].get_text(strip=True) if len(odds_elements) > 1 else 'N/A'
                    return over_close, under_close
                
                elif market_type == 'ah':
                    home_close = odds_elements[0].get_text(strip=True) if len(odds_elements) > 0 else 'N/A'
                    away_close = odds_elements[1].get_text(strip=True) if len(odds_elements) > 1 else 'N/A'
                    return home_close, away_close
            
            print(f"  ❌ Rand Betano negasit")
            return 'N/A', 'N/A'
            
        except Exception as e:
            print(f"  ❌ Eroare extragere cote: {e}")
            return 'N/A', 'N/A'
    
    try:
        # OVER/UNDER
        print("=== OVER/UNDER - EXTRAGERE LINII ===")
        response = requests.get(ou_link, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        lines_container = soup.select_one('div.min-md\\:px-\\[10px\\]')
        ou_lines = []
        
        if lines_container:
            line_elements = lines_container.find_all('p', string=re.compile(r'Over/Under'))
            print(f"Linii Over/Under găsite: {len(line_elements)}")
            
            for i, element in enumerate(line_elements[:10]):
                try:
                    line_text = element.get_text(strip=True)
                    print(f"\n--- Linia {i+1}: {line_text} ---")
                    
                    line_match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', line_text)
                    if line_match:
                        line_value = line_match.group(1)
                        display_line = f"+{line_value}"
                        print(f"✓ Valoare linie: {display_line}")
                        
                        base_url = ou_link.split('#')[0]
                        direct_url = f"{base_url}#over-under;1;{line_value};0"
                        print(f"✓ URL construit: {direct_url}")
                        
                        over_close, under_close = extract_betano_odds_from_url(direct_url, 'ou')
                        print(f"✓ Cote gasite: Over={over_close}, Under={under_close}")
                        
                        ou_lines.append({
                            'Line': display_line,
                            'Direct_URL': direct_url,
                            'Over_Close': over_close,
                            'Under_Close': under_close,
                            'Bookmaker': 'Betano.ro'
                        })
                        
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"✗ Eroare la linia {i+1}: {e}")
                    continue
        
        results['Over_Under_Lines'] = ou_lines
        
        # ASIAN HANDICAP
        print("\n\n=== ASIAN HANDICAP - EXTRAGERE LINII ===")
        response_ah = requests.get(ah_link, headers=headers)
        soup_ah = BeautifulSoup(response_ah.content, 'html.parser')
        
        ah_container = soup_ah.select_one('div.min-md\\:px-\\[10px\\]')
        ah_lines = []
        
        if ah_container:
            ah_elements = ah_container.find_all('p', string=re.compile(r'Asian Handicap'))
            print(f"Linii Asian Handicap găsite: {len(ah_elements)}")
            
            for i, element in enumerate(ah_elements[:10]):
                try:
                    line_text = element.get_text(strip=True)
                    print(f"\n--- Linia AH {i+1}: {line_text} ---")
                    
                    line_match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', line_text)
                    if line_match:
                        line_value = line_match.group(1)
                        clean_line = line_value.replace('+', '').replace('-', '')
                        print(f"✓ Valoare linie AH: {line_value}")
                        
                        base_url_ah = ah_link.split('#')[0]
                        direct_ah_url = f"{base_url_ah}#ah;1;{clean_line};0"
                        print(f"✓ URL AH construit: {direct_ah_url}")
                        
                        home_close, away_close = extract_betano_odds_from_url(direct_ah_url, 'ah')
                        print(f"✓ Cote AH gasite: Home={home_close}, Away={away_close}")
                        
                        ah_lines.append({
                            'Line': line_value,
                            'Direct_URL': direct_ah_url,
                            'Home_Close': home_close,
                            'Away_Close': away_close,
                            'Bookmaker': 'Betano.ro'
                        })
                        
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"✗ Eroare la linia AH {i+1}: {e}")
                    continue
        
        results['Handicap_Lines'] = ah_lines
        
        # Debug info
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'strategy': 'Parsing rapid cu BeautifulSoup',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        results['Error'] = f"Eroare generala: {str(e)}"
        print(f"❌ Eroare generala: {e}")
    
    return results

# NU mai este nevoie de această funcție separată - am unit totul
# def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
#     return scrape_oddsportal_complete(ou_link, ah_link)
