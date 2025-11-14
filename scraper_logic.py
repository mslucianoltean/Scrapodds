def scrape_via_api_fixed(ou_link, ah_link):
    import requests
    import re
    import json
    from collections import defaultdict
    
    results = {'Match': 'Scraping via API - Fixat'}
    
    try:
        # Extragem ID-ul meciului din link (corectat)
        match_id_match = re.search(r'/([a-zA-Z0-9-]+)-([a-zA-Z0-9]+)/', ou_link)
        if match_id_match:
            match_id = match_id_match.group(2)  # xYgsQpLr
            print(f"✓ ID meci extras: {match_id}")
        else:
            # Încercă alt pattern
            match_id_match = re.search(r'/([a-zA-Z0-9]+)$', ou_link.split('#')[0])
            if match_id_match:
                match_id = match_id_match.group(1)
                print(f"✓ ID meci extras (alt pattern): {match_id}")
            else:
                results['Error'] = "Nu s-a putut extrage ID-ul meciului"
                return results
        
        # Headers pentru a trece de securitate
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': ou_link,
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        # ----------------------------------------------------
        # ÎNCERCĂM ENDPOINT-URI COMUNE PENTRU ODDS PORTAL
        # ----------------------------------------------------
        
        api_endpoints = [
            f"https://fb.oddsportal.com/feed/match/{match_id}-1-2.dat",  # Cel mai comun
            f"https://www.oddsportal.com/feed/match/{match_id}-1-2.dat",
            f"https://fb.oddsportal.com/feed/match/1-1-{match_id}.dat",
            f"https://www.oddsportal.com/ajax/match/{match_id}/",
            f"https://www.oddsportal.com/feed/match/{match_id}",
            f"https://www.oddsportal.com/api/matches/{match_id}",
            f"https://fb.oddsportal.com/feed/match/{match_id}.dat",
        ]
        
        api_data = None
        
        for endpoint in api_endpoints:
            try:
                print(f"Încerc endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=10)
                
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                if response.status_code == 200:
                    content = response.text
                    print(f"✅ SUCCES la {endpoint} - Lungime: {len(content)}")
                    
                    if content.strip():
                        api_data = content
                        results['API_Endpoint'] = endpoint
                        results['API_Response_Length'] = len(content)
                        results['API_Response_Sample'] = content[:500]
                        
                        # Salvează răspunsul complet pentru analiză
                        with open(f'/tmp/oddsportal_api_{match_id}.txt', 'w') as f:
                            f.write(content)
                        print(f"✓ Răspuns salvat în /tmp/oddsportal_api_{match_id}.txt")
                        break
                    else:
                        print("✗ Răspuns gol")
                    
            except Exception as e:
                print(f"✗ {endpoint}: {e}")
                continue
        
        if not api_data:
            results['Error'] = "Niciun endpoint API nu a funcționat"
            return results
        
        # ----------------------------------------------------
        # PROCESSĂM DATELE API
        # ----------------------------------------------------
        
        # Încercă să parseze ca JSON
        try:
            # Curăță potențialul padding JSONP
            clean_data = api_data
            if clean_data.startswith('window.ODSData=') or clean_data.startswith('ODSData='):
                clean_data = re.sub(r'^[^=]*=', '', clean_data)
                clean_data = re.sub(r';$', '', clean_data)
            
            json_data = json.loads(clean_data)
            results['API_Data_Type'] = 'JSON'
            print("✅ Date JSON parsate cu succes")
            
            # Analizează structura JSON-ului
            analyze_json_structure(json_data)
            
            # Extrage cotele din JSON
            ou_lines = extract_from_json_advanced(json_data, "over-under")
            ah_lines = extract_from_json_advanced(json_data, "asian-handicap")
            
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Nu e JSON: {e}")
            results['API_Data_Type'] = 'RAW_TEXT'
            
            # Încearcă să extragi manual din text
            ou_lines = extract_from_text_advanced(api_data, "Over/Under")
            ah_lines = extract_from_text_advanced(api_data, "Asian Handicap")
            
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare API: {str(e)}"
    
    return results

def analyze_json_structure(json_data):
    """Analizează structura JSON-ului pentru a înțelege cum să extragem datele"""
    print("=== ANALIZĂ STRUCTURĂ JSON ===")
    
    def explore(obj, path="", depth=0):
        if depth > 3:  # Limită adâncimea
            return
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in ['odds', 'betano', 'over', 'under', 'handicap', 'market']:
                    print(f"🔍 Cheie importantă: {path}.{key} = {type(value)}")
                
                if isinstance(value, (dict, list)):
                    explore(value, f"{path}.{key}", depth + 1)
                    
        elif isinstance(obj, list) and len(obj) > 0:
            if len(obj) <= 3:  # Arată doar primele elemente
                for i, item in enumerate(obj[:3]):
                    explore(item, f"{path}[{i}]", depth + 1)
    
    explore(json_data)
    print("=== SFÂRȘIT ANALIZĂ ===")

def extract_from_json_advanced(json_data, market_type):
    """Extrage date din JSON folosind căutare avansată"""
    lines = []
    print(f"Extragere avansată din JSON pentru {market_type}...")
    
    betano_data_found = []
    
    def find_betano_and_odds(obj, path=""):
        if isinstance(obj, dict):
            # Verifică dacă este un obiect cu Betano
            if any('betano' in str(k).lower() for k in obj.keys()):
                betano_data_found.append({
                    'path': path,
                    'data': obj
                })
                print(f"✅ Betano object la: {path}")
            
            # Caută în continuare
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    find_betano_and_odds(value, f"{path}.{key}")
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_betano_and_odds(item, f"{path}[{i}]")
    
    # Execută căutarea
    find_betano_and_odds(json_data)
    
    print(f"Total obiecte Betano găsite: {len(betano_data_found)}")
    
    # Procesează datele găsite
    for betano_obj in betano_data_found[:5]:  # Primele 5
        print(f"Procesez: {betano_obj['path']}")
        # Aici vom extrage cotele după ce vedem structura
        
    return lines

def extract_from_text_advanced(text_data, market_type):
    """Extrage date din text folosind regex avansat"""
    lines = []
    print(f"Extragere avansată din text pentru {market_type}...")
    
    # Pattern-uri mai complexe pentru OddsPortal
    patterns = [
        # Pattern pentru structura de tip "Betano": {"odds": [1.85, 1.95]}
        r'"Betano[^"]*"[^}]*"odds"[^:]*:[\s]*\[([\d.,\s]+)\]',
        # Pattern pentru cote în apropiere de Betano
        r'Betano[^}]*?(\d+\.\d+)[^}]*?(\d+\.\d+)',
        # Pattern generic pentru cote
        r'(\d+\.\d+).*?Betano.*?(\d+\.\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_data, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"✓ Găsite {len(matches)} potriviri cu pattern: {pattern[:50]}...")
            for i, match in enumerate(matches[:3]):
                if isinstance(match, tuple) and len(match) >= 2:
                    odds = [str(odd).strip() for odd in match[:2]]
                    lines.append({
                        'Line': f'Linie {i+1}',
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Close': odds[0],
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Close': odds[1],
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Source': 'API_Text_Advanced'
                    })
                    print(f"  - Cote extrase: {odds[0]}/{odds[1]}")
            break
    
    return lines

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_via_api_fixed(ou_link, ah_link)
