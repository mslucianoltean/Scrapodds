import requests
from bs4 import BeautifulSoup
import re
import time

def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    """
    SCRAPING REAL - Extrage linii și cote de pe OddsPortal
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    results = {
        'Match': 'Scraping Real OddsPortal',
        'Over_Under_Lines': [],
        'Handicap_Lines': []
    }
    
    def extract_betano_odds(url, market_type):
        """Extrage cotele Betano dintr-un URL"""
        try:
            print(f"  📡 Accesez: {url}")
            response = requests.get(url, headers=headers, timeout=10)
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
        
        # OVER/UNDER - SCRAPING REAL
        print("🔍 Extrag linii Over/Under...")
        response_ou = requests.get(ou_link, headers=headers, timeout=10)
        soup_ou = BeautifulSoup(response_ou.content, 'html.parser')
        
        ou_lines = []
        
        # Găsește toate liniile Over/Under
        ou_elements = soup_ou.find_all('p', string=re.compile(r'Over/Under'))
        print(f"📊 Linii Over/Under găsite: {len(ou_elements)}")
        
        for i, element in enumerate(ou_elements[:8]):  # Primele 8 linii
            try:
                text = element.get_text(strip=True)
                match = re.search(r'Over/Under\s*\+?(\d+\.?\d*)', text)
                
                if match:
                    line_val = match.group(1)
                    display_line = f"+{line_val}"
                    
                    # Construiește URL
                    base_url = ou_link.split('#')[0]
                    direct_url = f"{base_url}#over-under;1;{line_val};0"
                    
                    print(f"  📈 Linia {i+1}: {display_line}")
                    
                    # Extrage cotele Betano
                    over_odd, under_odd = extract_betano_odds(direct_url, 'ou')
                    
                    ou_lines.append({
                        'Line': display_line,
                        'Over_Close': over_odd,
                        'Under_Close': under_odd,
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                    
                    time.sleep(1)  # Pauză între request-uri
                    
            except Exception as e:
                print(f"  ⚠️ Eroare linia {i+1}: {e}")
                continue
        
        # ASIAN HANDICAP - SCRAPING REAL  
        print("\n🔍 Extrag linii Asian Handicap...")
        response_ah = requests.get(ah_link, headers=headers, timeout=10)
        soup_ah = BeautifulSoup(response_ah.content, 'html.parser')
        
        ah_lines = []
        
        # Găsește toate liniile Asian Handicap
        ah_elements = soup_ah.find_all('p', string=re.compile(r'Asian Handicap'))
        print(f"📊 Linii Asian Handicap găsite: {len(ah_elements)}")
        
        for i, element in enumerate(ah_elements[:8]):  # Primele 8 linii
            try:
                text = element.get_text(strip=True)
                match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
                
                if match:
                    line_val = match.group(1)
                    clean_line = line_val.replace('+', '').replace('-', '')
                    
                    # Construiește URL
                    base_url = ah_link.split('#')[0]
                    direct_url = f"{base_url}#ah;1;{clean_line};0"
                    
                    print(f"  📈 Linia AH {i+1}: {line_val}")
                    
                    # Extrage cotele Betano
                    home_odd, away_odd = extract_betano_odds(direct_url, 'ah')
                    
                    ah_lines.append({
                        'Line': line_val,
                        'Home_Close': home_odd,
                        'Away_Close': away_odd,
                        'Bookmaker': 'Betano.ro',
                        'Direct_URL': direct_url
                    })
                    
                    time.sleep(1)  # Pauză între request-uri
                    
            except Exception as e:
                print(f"  ⚠️ Eroare linia AH {i+1}: {e}")
                continue
        
        # Salvează rezultatele
        results['Over_Under_Lines'] = ou_lines
        results['Handicap_Lines'] = ah_lines
        
        results['Debug'] = {
            'ou_lines_found': len(ou_lines),
            'ah_lines_found': len(ah_lines),
            'strategy': 'Scraping real cu BeautifulSoup',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ SCRAPING COMPLETAT: {len(ou_lines)} linii OU, {len(ah_lines)} linii AH")
        
    except Exception as e:
        results['Error'] = f"Eroare generală: {str(e)}"
        print(f"❌ EROARE: {e}")
    
    return results
