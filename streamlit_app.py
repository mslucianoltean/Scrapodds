import streamlit as st
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import json
import re

class OddsScraper:
    def __init__(self, debug=False):
        chrome_options = Options()
        if not debug:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.actions = webdriver.ActionChains(self.driver)
        self.debug = debug
    
    def take_screenshot(self, name):
        """Take screenshot for debugging"""
        if self.debug:
            self.driver.save_screenshot(f"{name}.png")
            st.image(f"{name}.png", caption=name, use_column_width=True)
    
    def extract_line_value(self, line_element):
        """Extract the line value from the element, handling different formats"""
        try:
            # Try different XPath patterns to find the line text
            selectors = [
                './/p[contains(@class, "max-sm")]',
                './/span[contains(@class, "flex")]//span',
                './/p[contains(text(), "Over/Under")]',
                './/span[contains(text(), "Over/Under")]'
            ]
            
            for selector in selectors:
                try:
                    element = line_element.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except:
                    continue
            
            # If no specific element found, get all text and find the line
            full_text = line_element.text
            # Look for patterns like "Over/Under +2.5" or similar
            pattern = r'Over/Under\s*[+-]?\d+\.?\d*'
            match = re.search(pattern, full_text)
            if match:
                return match.group()
                
            return full_text
        except:
            return "Unknown"
    
    def find_line_by_partial_match(self, line_elements, target_lines):
        """Find lines that partially match the target lines"""
        matches = {}
        
        for line_element in line_elements:
            line_value = self.extract_line_value(line_element)
            
            # Check if this line contains any of our target patterns
            for target in target_lines:
                # For simple inputs like "cl", look for common patterns
                if target.lower() == 'cl':
                    if any(pattern in line_value for pattern in ['+2.25', '+2.5', '+2.75', '2.25', '2.5', '2.75']):
                        matches['cl'] = line_element
                elif target.lower() == 'm3':
                    if any(pattern in line_value for pattern in ['+3.25', '+3.5', '+3.75', '3.25', '3.5', '3.75']):
                        matches['m3'] = line_element
                elif target.lower() == 'm2':
                    if any(pattern in line_value for pattern in ['+2.75', '+3.0', '+3.25', '2.75', '3.0', '3.25']):
                        matches['m2'] = line_element
                elif target.lower() == 'm1':
                    if any(pattern in line_value for pattern in ['+2.25', '+2.5', '+2.75', '2.25', '2.5', '2.75']):
                        matches['m1'] = line_element
                elif target.lower() == 'p1':
                    if any(pattern in line_value for pattern in ['+1.75', '+2.0', '+2.25', '1.75', '2.0', '2.25']):
                        matches['p1'] = line_element
                elif target.lower() == 'p2':
                    if any(pattern in line_value for pattern in ['+1.25', '+1.5', '+1.75', '1.25', '1.5', '1.75']):
                        matches['p2'] = line_element
                elif target.lower() == 'p3':
                    if any(pattern in line_value for pattern in ['+0.75', '+1.0', '+1.25', '0.75', '1.0', '1.25']):
                        matches['p3'] = line_element
                # Also try direct partial match
                elif target.lower() in line_value.lower():
                    matches[target] = line_element
            
            st.info(f"Line text: '{line_value}'")
        
        return matches
    
    def scrape_over_under_odds(self, url, lines):
        try:
            st.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(5)
            self.take_screenshot("01_initial_page")
            
            results = {}
            
            # Find all line elements in Over/Under tab
            st.info("Looking for line elements...")
            line_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "border-black-borders") and contains(@class, "hover:bg-gray-light") and contains(@class, "flex") and contains(@class, "h-9") and contains(@class, "cursor-pointer")]')
            
            st.info(f"Found {len(line_elements)} line elements")
            
            # Find matching lines using partial matching
            matched_lines = self.find_line_by_partial_match(line_elements, lines)
            st.info(f"Found {len(matched_lines)} matching lines: {list(matched_lines.keys())}")
            
            for line_name, line_element in matched_lines.items():
                try:
                    st.success(f"✓ Processing line: {line_name}")
                    
                    # Get the full line text for display
                    line_value = self.extract_line_value(line_element)
                    st.info(f"Full line text: {line_value}")
                    
                    # Click to expand the line
                    st.info(f"Clicking to expand line...")
                    line_element.click()
                    time.sleep(3)
                    self.take_screenshot(f"02_line_expanded_{line_name}")
                    
                    # Look for Betano in the expanded section
                    try:
                        st.info("Looking for Betano...")
                        # Find Betano element
                        betano_selectors = [
                            '//a[contains(., "Betano")]',
                            '//span[contains(., "Betano")]',
                            '//div[contains(., "Betano")]',
                            '//*[contains(text(), "Betano")]'
                        ]
                        
                        betano_element = None
                        for selector in betano_selectors:
                            try:
                                elements = self.driver.find_elements(By.XPATH, selector)
                                for elem in elements:
                                    if "betano" in elem.text.lower():
                                        betano_element = elem
                                        st.success(f"✓ Found Betano: {betano_element.text}")
                                        break
                                if betano_element:
                                    break
                            except:
                                continue
                        
                        if betano_element:
                            # Find the Betano row
                            betano_row = betano_element.find_element(By.XPATH, './ancestor::div[contains(@class, "flex")][1]')
                            
                            # Find all clickable elements in the Betano row
                            clickable_elements = betano_row.find_elements(By.XPATH, './/p[contains(@class, "cursor-pointer")] | .//div[contains(@class, "cursor-pointer")] | .//button')
                            
                            st.info(f"Found {len(clickable_elements)} clickable elements in Betano row")
                            
                            # Try to click the first two (Over and Under)
                            over_open, over_close, under_open, under_close = "N/A", "N/A", "N/A", "N/A"
                            
                            if len(clickable_elements) >= 2:
                                # Click Over (first element)
                                try:
                                    st.info("Clicking Over button...")
                                    clickable_elements[0].click()
                                    time.sleep(2)
                                    self.take_screenshot(f"03_over_popup_{line_name}")
                                    
                                    # Extract OVER odds
                                    over_open, over_close = self.extract_popup_odds("Over")
                                    
                                    # Close popup
                                    self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                                    time.sleep(1)
                                except Exception as e:
                                    st.warning(f"Could not process Over: {e}")
                                
                                # Click Under (second element)
                                try:
                                    st.info("Clicking Under button...")
                                    clickable_elements[1].click()
                                    time.sleep(2)
                                    self.take_screenshot(f"04_under_popup_{line_name}")
                                    
                                    # Extract UNDER odds
                                    under_open, under_close = self.extract_popup_odds("Under")
                                    
                                    # Close popup
                                    self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                                    time.sleep(1)
                                except Exception as e:
                                    st.warning(f"Could not process Under: {e}")
                            
                            # Store results
                            results[line_name] = {
                                'line_value': line_value,
                                'over_open': over_open,
                                'over_close': over_close,
                                'under_open': under_open,
                                'under_close': under_close
                            }
                            
                        else:
                            st.warning("✗ Could not find Betano")
                            
                    except Exception as e:
                        st.error(f"Error with Betano for line {line_name}: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error processing line {line_name}: {str(e)}")
            
            return results
            
        except Exception as e:
            st.error(f"Error scraping Over/Under: {str(e)}")
            return {}
    
    def extract_popup_odds(self, bet_type):
        """Extract open and close odds from popup"""
        open_odds, close_odds = "N/A", "N/A"
        
        try:
            # Try multiple XPath patterns for open odds
            open_selectors = [
                '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]',
                '//div[contains(text(), "Opening")]/following-sibling::div',
                '//div[contains(@class, "open")]',
                '//span[contains(text(), "Open")]/following-sibling::span'
            ]
            
            for selector in open_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.text.strip():
                        open_odds = element.text.strip()
                        st.success(f"{bet_type} Open: {open_odds}")
                        break
                except:
                    continue
            
            # Try multiple XPath patterns for close odds
            close_selectors = [
                '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[2]/div/div/div[2]/div',
                '//div[contains(text(), "Closing")]/following-sibling::div',
                '//div[contains(@class, "close")]',
                '//span[contains(text(), "Close")]/following-sibling::span'
            ]
            
            for selector in close_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.text.strip():
                        close_odds = element.text.strip()
                        st.success(f"{bet_type} Close: {close_odds}")
                        break
                except:
                    continue
                    
        except Exception as e:
            st.warning(f"Error extracting {bet_type} odds: {e}")
        
        return open_odds, close_odds
    
    def close(self):
        self.driver.quit()

def main():
    st.title("OddsPortal Smart Scraper")
    
    st.info("🎯 This version uses smart matching for lines like 'cl', 'm3', etc.")
    
    # Input section
    url = st.text_input("Enter OddsPortal URL:", placeholder="https://www.oddsportal.com/...")
    
    over_under_lines = st.text_input("Lines to scrape (comma-separated):", value="cl, m3, m2, m1, p1, p2, p3")
    
    st.info("""
    **Line mappings:**
    - **cl**: +2.25, +2.5, +2.75
    - **m3**: +3.25, +3.5, +3.75  
    - **m2**: +2.75, +3.0, +3.25
    - **m1**: +2.25, +2.5, +2.75
    - **p1**: +1.75, +2.0, +2.25
    - **p2**: +1.25, +1.5, +1.75
    - **p3**: +0.75, +1.0, +1.25
    """)
    
    if st.button("Scrape Over/Under Odds"):
        if url and over_under_lines:
            lines = [line.strip() for line in over_under_lines.split(",")]
            
            with st.spinner("Scraping with smart line matching..."):
                scraper = OddsScraper(debug=True)
                try:
                    results = scraper.scrape_over_under_odds(url, lines)
                    
                    if results:
                        st.success("🎉 Successfully scraped Over/Under odds!")
                        
                        # Create DataFrame for display
                        data = []
                        for line_name, odds_data in results.items():
                            data.append({
                                'Line': line_name,
                                'Full Text': odds_data.get('line_value', ''),
                                'Over Open': odds_data.get('over_open', 'N/A'),
                                'Over Close': odds_data.get('over_close', 'N/A'),
                                'Under Open': odds_data.get('under_open', 'N/A'),
                                'Under Close': odds_data.get('under_close', 'N/A')
                            })
                        
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                        
                        # Download JSON
                        json_data = json.dumps(results, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name="odds_results.json",
                            mime="application/json"
                        )
                    else:
                        st.error("❌ No odds found. Check the debug information above.")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    scraper.close()
        else:
            st.warning("Please enter both URL and lines.")

if __name__ == "__main__":
    main()
                          
                               
            
           
            
          
                     
   
      
