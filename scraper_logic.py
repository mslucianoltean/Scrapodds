def scrape_via_api_fixed_v2(ou_link, ah_link):
    import requests
    import re
    import json
    import time
    from collections import defaultdict
    
    results = {'Match': 'Scraping via API - Fixat V2'}
    
    try:
        # Extragem ID-ul meciului
        match_id_match = re.search(r'/([a-zA-Z0-9-]+)-([a-zA-Z0-9]+)/', ou_link)
        if match_id_match:
            match_id = match_id_match.group(2)
            print(f"✓ ID meci extras: {match_id}")
        else:
            results['Error'] = "Nu s-a putut extrage ID-ul meciului"
            return results
        
        # Headers mai complet pentru a trece de securitate
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ro;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.oddsportal.com/',
            'Origin': 'https://www.oddsportal.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Connection': 'keep-alive',
        }
        
        # Adaugă cookies pentru a imita un browser real
        cookies = {
            'oddsportal': '1',
            'oddsportal_session': '1',
        }
        
        # ----------------------------------------------------
        # ÎNCERCĂM ENDPOINT-URI ALTERNATIVE
        # ----------------------------------------------------
        
        api_endpoints = [
            # Endpoint-uri principale
            f"https://fb.oddsportal.com/feed/match/{match_id}-1-2.dat?={int(time.time())}",
            f"https://www.oddsportal.com/feed/match/{match_id}-1-2.dat?={int(time.time())}",
            
            # Endpoint-uri alternative
            f"https://fb.oddsportal.com/feed/match/1-1-{match_id}.dat",
            f"https://www.oddsportal.com/ajax/match/{match_id}/",
            
            # Endpoint-uri cu parametri diferiți
            f"https://fb.oddsportal.com/feed/match/{match_id}.dat",
            f"https://www.oddsportal.com/api/v1/matches/{match_id}",
            
            # Endpoint pentru basketball specific
            f"https://fb.oddsportal.com/feed/basketball/usa/nba/{match_id}.dat",
        ]
        
        api_data = None
        
        for endpoint in api_endpoints:
            try:
                print(f"Încerc endpoint: {endpoint}")
                
                # Adaugă timestamp pentru a evita cache-ul
                if '?' not in endpoint:
                    endpoint += f"?_={int(time.time())}"
                
                response = requests.get(endpoint, headers=headers, cookies=cookies, timeout=15)
                
                print(f"Status: {response.status_code}")
                print(f"Content-Length: {len(response.text)}")
                
                if response.status_code == 200:
                    content = response.text
                    print(f"✅ SUCCES la {endpoint} - Lungime: {len(content)}")
                    
                    if content.strip() and len(content) > 10:  # Verifică că nu e mesaj de eroare
                        api_data = content
                        results['API_Endpoint'] = endpoint
                        results['API_Response_Length'] = len(content)
                        results['API_Response_Sample'] = content[:500] if len(content) > 500 else content
                        
                        # Salvează răspunsul complet
                        with open(f'/tmp/oddsportal_response_{match_id}.txt', 'w') as f:
                            f.write(content)
                        print(f"✓ Răspuns salvat: /tmp/oddsportal_response_{match_id}.txt")
                        break
                    else:
                        print("✗ Răspuns prea scurt sau gol")
                else:
                    print(f"✗ Status code: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Eroare: {e}")
                continue
        
        if not api_data:
            # Încercă o abordare diferită - să folosim Selenium pentru a extrage datele din network tab
            results['Error'] = "Toate endpoint-urile au returnat eroare. Încerc abordare Selenium..."
            return scrape_via_selenium_network(ou_link, ah_link, match_id)
        
        # ----------------------------------------------------
        # PROCESSĂM DATELE API
        # ----------------------------------------------------
        
        # Încercă să parseze ca JSON
        try:
            # Curăță potențialul padding JSONP
            clean_data = api_data.strip()
            
            # Îndepărtează prefixele JSONP comune
            jsonp_prefixes = ['window.ODSData=', 'ODSData=', 'jsonCallback(', 'callback(']
            for prefix in jsonp_prefixes:
                if clean_data.startswith(prefix):
                    clean_data = clean_data[len(prefix):]
                    # Îndepărtează sufixul )
                    if clean_data.endswith(');'):
                        clean_data = clean_data[:-2]
                    elif clean_data.endswith(');'):
                        clean_data = clean_data[:-1]
                    break
            
            json_data = json.loads(clean_data)
            results['API_Data_Type'] = 'JSON'
            print("✅ Date JSON parsate cu succes")
            
            # Extrage cotele din JSON
            ou_lines = extract_data_from_json(json_data, "over-under")
            ah_lines = extract_data_from_json(json_data, "asian-handicap")
            
            results['Over_Under_Lines'] = ou_lines
            results['Handicap_Lines'] = ah_lines
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Nu e JSON, încerc parsare text: {e}")
            results['API_Data_Type'] = 'RAW_TEXT'
            
            # Verifică dacă conține date utile
            if 'Betano' in api_data or 'betano' in api_data.lower():
                print("✓ Betano găsit în răspunsul text")
                ou_lines = extract_from_text_simple(api_data, "Over/Under")
                ah_lines = extract_from_text_simple(api_data, "Asian Handicap")
                
                results['Over_Under_Lines'] = ou_lines
                results['Handicap_Lines'] = ah_lines
            else:
                print("✗ Betano nu este în răspuns")
                results['Over_Under_Lines'] = []
                results['Handicap_Lines'] = []
        
    except Exception as e:
        results['Error'] = f"Eroare API: {str(e)}"
    
    return results

def extract_data_from_json(json_data, market_type):
    """Extrage date din JSON"""
    lines = []
    print(f"Extragere {market_type} din JSON...")
    
    # Funcție recursivă pentru a explora JSON-ul
    def explore_json(obj, path=""):
        findings = []
        
        if isinstance(obj, dict):
            # Verifică chei relevante
            for key, value in obj.items():
                key_str = str(key).lower()
                
                # Verifică dacă este bookmaker Betano
                if 'betano' in key_str:
                    print(f"✅ Betano găsit la: {path}.{key}")
                    findings.append({'type': 'betano', 'path': f"{path}.{key}", 'data': value})
                
                # Verifică pentru cote
                elif any(odds_key in key_str for odds_key in ['odds', 'price', 'value', 'over', 'under']):
                    if isinstance(value, (int, float)) or (isinstance(value, str) and '.' in value):
                        print(f"📊 Cotă găsită: {path}.{key} = {value}")
                        findings.append({'type': 'odds', 'path': f"{path}.{key}", 'value': value})
                
                # Explorează recursiv
                if isinstance(value, (dict, list)):
                    findings.extend(explore_json(value, f"{path}.{key}"))
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                findings.extend(explore_json(item, f"{path}[{i}]"))
        
        return findings
    
    # Execută explorarea
    findings = explore_json(json_data)
    
    # Procesează findings
    betano_data = [f for f in findings if f['type'] == 'betano']
    odds_data = [f for f in findings if f['type'] == 'odds']
    
    print(f"Betano findings: {len(betano_data)}")
    print(f"Odds findings: {len(odds_data)}")
    
    # Creează linii bazate pe findings
    if betano_data and odds_data:
        # Grupează cotele (presupunem primele 2 cote pentru Betano)
        if len(odds_data) >= 2:
            lines.append({
                'Line': 'Extras din JSON',
                f'{"Over" if market_type == "over-under" else "Home"}_Close': odds_data[0]['value'],
                f'{"Over" if market_type == "over-under" else "Home"}_Open': 'N/A',
                f'{"Under" if market_type == "over-under" else "Away"}_Close': odds_data[1]['value'],
                f'{"Under" if market_type == "over-under" else "Away"}_Open': 'N/A',
                'Bookmaker': 'Betano.ro',
                'Source': 'JSON_API'
            })
    
    return lines

def extract_from_text_simple(text_data, market_type):
    """Extrage date simple din text"""
    lines = []
    
    # Caută pattern-uri simple
    patterns = [
        r'(\d+\.\d+).*?Betano.*?(\d+\.\d+)',
        r'Betano.*?(\d+\.\d+).*?(\d+\.\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_data, re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 2:
                    lines.append({
                        'Line': 'Extras din text',
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Close': match[0],
                        f'{"Over" if market_type == "Over/Under" else "Home"}_Open': 'N/A',
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Close': match[1],
                        f'{"Under" if market_type == "Over/Under" else "Away"}_Open': 'N/A',
                        'Bookmaker': 'Betano.ro',
                        'Source': 'Text_API'
                    })
            break
    
    return lines

def scrape_via_selenium_network(ou_link, ah_link, match_id):
    """Folosește Selenium pentru a captura request-urile de network"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import os
    
    results = {'Match': 'Scraping via Selenium Network'}
    
    # Această funcție ar necesita setup de Chrome cu logging pentru network
    # Este mai complexă și o putem implementa dacă API-ul direct nu funcționează
    
    results['Error'] = "Abordarea Selenium Network necesită setup avansat"
    return results

# FOLOSEȘTE ACEST COD!
def scrape_basketball_match_full_data_filtered(ou_link, ah_link):
    return scrape_via_api_fixed_v2(ou_link, ah_link)
