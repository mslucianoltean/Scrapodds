def scrape_via_api(ou_link, ah_link):
    import requests
    import re
    import json
    from collections import defaultdict
    
    results = {'Match': 'Scraping via API'}
    
    try:
        # Extragem ID-ul meciului din link
        match_id_match = re.search(r'/([a-zA-Z0-9]+)/#', ou_link)
        if match_id_match:
            match_id = match_id_match.group(1)
            print(f"✓ ID meci extras: {match_id}")
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
        ]
        
        api_data = None
        
        for endpoint in api_endpoints:
            try:
                print(f"Încerc endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ SUCCES la {endpoint}")
                    
                    # Verifică tipul de răspuns
                    content = response.text
                    if content.strip():
                        api_data = content
                        results['API_Endpoint'] = endpoint
                        results['API_Response_Length'] = len(content)
                        results['API_Response_Sample'] = content[:500]
                        break
                    
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
            json_data = json.loads(api_data)
            results['API_Data'] = json_data
            print("✅ Date JSON parsate cu succes")
            
            # Extrage cotele din JSON
            ou_lines = extract_from_json(json_data, "over-under")
            ah_lines = extract_from_json(json_data, "asian-handicap")
            
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
            
        except json.JSONDecodeError:
            # Poate e alt format (like .dat)
            print("⚠️ Răspunsul nu e JSON, încerc altă parsare...")
            results['Raw_API_Data'] = api_data
            
            # Încearcă să extragi manual din text
            ou_lines = extract_from_text(api_data, "Over/Under")
            ah_lines = extract_from_text(api_data, "Asian Handicap")
            
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
        
    except Exception as e:
        results['Error'] = f"Eroare API: {str(e)}"
    
    return results

def extract_from_json(json_data, market_type):
    """Extrage date din JSON"""
    lines = []
    print(f"Extragere din JSON pentru {market_type}...")
    
    # Această funcție trebuie adaptată la structura reală a JSON-ului
    # Vom face o căutare recursivă pentru Betano și cote
    
    def find_betano_data(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    find_betano_data(value, f"{path}.{key}")
                elif key == "Betano" or (isinstance(value, str) and "betano" in value.lower()):
                    print(f"✓ Betano găsit la: {path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_betano_data(item, f"{path}[{i}]")
    
    # Caută Betano în JSON
    find_betano_data(json_data)
    
    # TODO: Adaptează această logică la structura reală a JSON-ului
    # După ce vedem cum arată JSON-ul, putem extrage datele corect
    
    return lines

def extract_from_text(text_data, market_type):
    """Extrage date din text/raw data"""
    lines = []
    print(f"Extragere din text pentru {market_type}...")
    
    # Caută Betano și cote în text
    betano_patterns = [
        r'Betano[^>]*?(\d+\.\d+)[^>]*?(\d+\.\d+)',
        r'(\d+\.\d+).*?Betano.*?(\d+\.\d+)',
    ]
    
    for pattern in betano_patterns:
        matches = re.findall(pattern, text_data, re.IGNORECASE)
        if matches:
            print(f"✓ Găsite {len(matches)} potriviri pentru {market_type}")
            for i, match in enumerate(matches[:3]):
                if len(match) >= 2:
                    lines.append({
                        'Line': f'Linie {i+1}',
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Close': match[0],
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Close': match[1],
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Source': 'API_Text'
                    })
            break
    
    return lines

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_via_api(ou_link, ah_link)
