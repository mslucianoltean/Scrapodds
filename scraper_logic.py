# După secțiunea Over/Under, adaugă:

print("\n🔍 ASIAN HANDICAP - Încep extragerea...")
driver.get(ah_link)
time.sleep(10)

ah_lines = []

# Încearcă aceiași strategie ca pentru Over/Under
ah_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Asian Handicap')]")
print(f"📊 Elemente AH găsite: {len(ah_elements)}")

for i, element in enumerate(ah_elements[:10]):
    try:
        text = element.text.strip()
        if text and 'Asian Handicap' in text:
            print(f"  {i+1}. {text}")
            
            match = re.search(r'Asian Handicap\s*([+-]?\d+\.?\d*)', text)
            if match:
                line_val = match.group(1)
                clean_val = line_val.replace('+', '').replace('-', '')
                print(f"  ✅ LINIE AH: {line_val}")
                
                base_url = ah_link.split('#')[0]
                direct_url = f"{base_url}#ah;1;{clean_val};0"
                
                driver.get(direct_url)
                time.sleep(8)
                
                # Aceeași logică îmbunătățită pentru Betano
                home_odd, away_odd = 'N/A', 'N/A'
                betano_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'betano')]")
                
                for betano_element in betano_elements:
                    try:
                        betano_row = betano_element
                        for _ in range(4):
                            betano_row = betano_row.find_element(By.XPATH, "./..")
                            if betano_row.tag_name == 'tr':
                                break
                        
                        odds_selectors = [
                            ".//p[contains(@class, 'odds-text')]",
                            ".//p[contains(@class, 'odds')]",
                            ".//span[contains(@class, 'odds')]",
                            ".//div[contains(@class, 'odds')]"
                        ]
                        
                        for selector in odds_selectors:
                            odds_elements = betano_row.find_elements(By.XPATH, selector)
                            if len(odds_elements) >= 2:
                                home_odd = odds_elements[0].text.strip()
                                away_odd = odds_elements[1].text.strip()
                                if any(c.isdigit() for c in home_odd) and any(c.isdigit() for c in away_odd):
                                    print(f"  ✅ COTE AH: Home={home_odd}, Away={away_odd}")
                                    break
                    except:
                        continue
                
                ah_lines.append({
                    'Line': line_val,
                    'Home_Close': home_odd,
                    'Away_Close': away_odd,
                    'Bookmaker': 'Betano.ro',
                    'Direct_URL': direct_url
                })
                
                driver.get(ah_link)
                time.sleep(5)
                
    except Exception as e:
        print(f"  ⚠️ Eroare AH {i+1}: {e}")
        continue
