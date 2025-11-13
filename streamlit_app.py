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
        """Extract the line value from the element"""
        try:
            # Look for the exact pattern you showed: <p class="max-sm:!hidden">Over/Under +228.5</p>
            selectors = [
                './/p[contains(@class, "max-sm")]',
                './/p[contains(text(), "Over/Under")]',
                './/span[contains(text(), "Over/Under")]',
                './/div[contains(text(), "Over/Under")]'
            ]
            
            for selector in selectors:
                try:
                    element = line_element.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text and "Over/Under" in text:
                        return text
                except:
                    continue
            
            # Fallback: get all text from the element
            return line_element.text.strip()
        except:
            return "Unknown"
    
    def find_matching_lines(self, line_elements, target_lines):
        """Find lines that match the target lines exactly or partially"""
        matches = {}
        
        st.info("Scanning all available lines:")
        for line_element in line_elements:
            line_value = self.extract_line_value(line_element)
            st.info(f"Found line: '{line_value}'")
            
            # Check if this line matches any of our target lines
            for target in target_lines:
                # Try exact match first
                if target.lower() in line_value.lower():
                    matches[target] = {
                        'element': line_element,
                        'full_text': line_value
                    }
                    st.success(f"✓ MATCH: '{target}' found in '{line_value}'")
                    break
                # Also try to match the number part if target is a number
                elif target.replace('.', '').isdigit():
                    if target in line_value:
                        matches[target] = {
                            'element': line_element, 
                            'full_text': line_value
                        }
                        st.success(f"✓ MATCH: '{target}' found in '{line_value}'")
                        break
        
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
            
            # Find matching lines
            matched_lines = self.find_matching_lines(line_elements, lines)
            st.info(f"Found {len(matched_lines)} matching lines: {list(matched_lines.keys())}")
            
            for line_name, line_data in matched_lines.items():
                try:
                    line_element = line_data['element']
                    full_text = line_data['full_text']
                    
                    st.success(f"✓ Processing: {line_name} (Full text: {full_text})")
                    
                    # Click to expand the line
                    st.info("Clicking to expand line...")
                    line_element.click()
                    time.sleep(3)
                    self.take_screenshot(f"02_line_expanded_{line_name}")
                    
                    # Look for Betano
                    betano_found = self.find_and_click_betano(line_name)
                    
                    if betano_found:
                        # Extract odds
                        odds_data = self.extract_betano_odds(line_name)
                        results[line_name] = {
                            'full_line_text': full_text,
                            **odds_data
                        }
                    else:
                        st.warning(f"Could not find Betano for line {line_name}")
                        results[line_name] = {
                            'full_line_text': full_text,
                            'over_open': 'N/A',
                            'over_close': 'N/A', 
                            'under_open': 'N/A',
                            'under_close': 'N/A'
                        }
                        
                except Exception as e:
                    st.error(f"Error processing line {line_name}: {str(e)}")
            
            return results
            
        except Exception as e:
            st.error(f"Error scraping Over/Under: {str(e)}")
            return {}
    
    def find_and_click_betano(self, line_name):
        """Find and click Betano odds"""
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
            
            if not betano_element:
                st.warning("✗ Betano not found")
                return False
            
            # Find the Betano row
            betano_row = betano_element.find_element(By.XPATH, './ancestor::div[contains(@class, "flex")][1]')
            
            # Find clickable odds buttons in Betano row
            clickable_elements = betano_row.find_elements(By.XPATH, './/p[contains(@class, "cursor-pointer")] | .//div[contains(@class, "cursor-pointer")] | .//button | .//a')
            
            st.info(f"Found {len(clickable_elements)} clickable elements in Betano row")
            
            if len(clickable_elements) >= 2:
                return True
            else:
                st.warning("Not enough clickable elements found for Betano")
                return False
                
        except Exception as e:
            st.error(f"Error finding Betano: {str(e)}")
            return False
    
    def extract_betano_odds(self, line_name):
        """Extract Over/Under odds from Betano"""
        over_open, over_close, under_open, under_close = "N/A", "N/A", "N/A", "N/A"
        
        try:
            # Find Betano row again
            betano_element = self.driver.find_element(By.XPATH, '//*[contains(text(), "Betano")]')
            betano_row = betano_element.find_element(By.XPATH, './ancestor::div[contains(@class, "flex")][1]')
            clickable_elements = betano_row.find_elements(By.XPATH, './/p[contains(@class, "cursor-pointer")] | .//div[contains(@class, "cursor-pointer")] | .//button | .//a')
            
            # Click Over (first element)
            if len(clickable_elements) >= 1:
                st.info("Clicking Over button...")
                clickable_elements[0].click()
                time.sleep(2)
                self.take_screenshot(f"03_over_popup_{line_name}")
                
                over_open, over_close = self.extract_popup_odds("Over")
                self.close_popup()
            
            # Click Under (second element)  
            if len(clickable_elements) >= 2:
                st.info("Clicking Under button...")
                clickable_elements[1].click()
                time.sleep(2)
                self.take_screenshot(f"04_under_popup_{line_name}")
                
                under_open, under_close = self.extract_popup_odds("Under")
                self.close_popup()
                
        except Exception as e:
            st.error(f"Error extracting Betano odds: {str(e)}")
        
        return {
            'over_open': over_open,
            'over_close': over_close,
            'under_open': under_open,
            'under_close': under_close
        }
    
    def extract_popup_odds(self, bet_type):
        """Extract open and close odds from popup"""
        open_odds, close_odds = "N/A", "N/A"
        
        try:
            # Try multiple XPath patterns for open odds
            open_selectors = [
                '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]',
                '//div[contains(text(), "Opening")]/following-sibling::div',
                '//span[contains(text(), "Open")]/following-sibling::span',
                '//div[contains(@class, "open")]'
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
                '//span[contains(text(), "Close")]/following-sibling::span',
                '//div[contains(@class, "close")]'
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
    
    def close_popup(self):
        """Close the popup"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
            time.sleep(1)
        except:
            pass
    
    def close(self):
        self.driver.quit()

def main():
    st.title("OddsPortal Exact Match Scraper")
    
    st.info("🔍 **Enter the EXACT text that appears in the Over/Under lines**")
    st.info("Example: If you see 'Over/Under +228.5', enter '+228.5' or 'Over/Under +228.5'")
    
    # Input section
    url = st.text_input("Enter OddsPortal URL:", placeholder="https://www.oddsportal.com/...")
    
    lines_input = st.text_input("Enter EXACT line texts to scrape (comma-separated):", 
                               placeholder="+228.5, +3.5, +2.5, Over/Under +228.5, etc.")
    
    if st.button("Scrape Over/Under Odds"):
        if url and lines_input:
            lines = [line.strip() for line in lines_input.split(",")]
            
            st.info(f"Looking for these exact lines: {lines}")
            
            with st.spinner("Scraping with exact text matching..."):
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
                                'Full Text': odds_data.get('full_line_text', ''),
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
                        st.error("❌ No matching lines found. Check the debug output above to see what lines are available.")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    scraper.close()
        else:
            st.warning("Please enter both URL and lines.")

if __name__ == "__main__":
    main()
