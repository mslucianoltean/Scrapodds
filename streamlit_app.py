import streamlit as st
import pandas as pd
import json
import time
import os

# Try to import undetected_chromedriver, fall back to regular selenium
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

class OddsScraper:
    def __init__(self, debug=False):
        self.debug = debug
        self.driver = self.setup_driver()
    
    def setup_driver(self):
        """Setup ChromeDriver for Streamlit Cloud"""
        if UC_AVAILABLE:
            # Use undetected_chromedriver (more reliable)
            st.info("🚀 Using undetected_chromedriver...")
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--remote-debugging-port=9222")
            
            driver = uc.Chrome(options=options)
            return driver
        else:
            # Fallback to regular selenium
            st.info("🚀 Using regular ChromeDriver...")
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            except Exception as e:
                st.error(f"❌ ChromeDriver setup failed: {e}")
                raise
    
    def take_screenshot(self, name):
        """Take screenshot for debugging"""
        if self.debug:
            try:
                self.driver.save_screenshot(f"{name}.png")
                st.image(f"{name}.png", caption=name, use_column_width=True)
            except:
                pass
    
    def scrape_over_under_odds(self, url, lines):
        try:
            st.info(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(10)  # Wait longer for initial load
            
            self.take_screenshot("01_page_loaded")
            
            # Wait for page to load completely
            time.sleep(5)
            
            results = {}
            
            # Find all line elements with multiple selector strategies
            st.info("🔍 Searching for line elements...")
            
            # Try different selectors for line elements
            line_selectors = [
                '//div[contains(@class, "border-black-borders")]',
                '//div[contains(@class, "cursor-pointer")]',
                '//div[contains(@class, "hover:bg-gray-light")]',
                '//div[@class="flex h-9 cursor-pointer border-b border-l border-r border-black-borders hover:bg-gray-light text-xs"]'
            ]
            
            line_elements = []
            for selector in line_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        line_elements.extend(elements)
                        st.info(f"✅ Found {len(elements)} elements with: {selector}")
                        break
                except:
                    continue
            
            if not line_elements:
                # Last resort: get all divs and filter
                all_divs = self.driver.find_elements(By.XPATH, '//div')
                line_elements = [div for div in all_divs if div.get_attribute('class') and 'border-black-borders' in div.get_attribute('class')]
            
            st.info(f"📊 Total line elements found: {len(line_elements)}")
            
            # Show what we found
            for i, elem in enumerate(line_elements[:10]):  # Show first 10
                try:
                    text = elem.text.strip()
                    if text:
                        st.info(f"Line {i+1}: '{text}'")
                except:
                    pass
            
            processed_count = 0
            max_lines_to_process = min(3, len(lines))  # Process max 3 lines to avoid timeout
            
            for i, line_element in enumerate(line_elements):
                if processed_count >= max_lines_to_process:
                    break
                    
                try:
                    line_text = line_element.text.strip()
                    if not line_text or "Over/Under" not in line_text:
                        continue
                    
                    st.info(f"📝 Checking: '{line_text}'")
                    
                    # Check for matches
                    matched_line = None
                    for target in lines:
                        if target in line_text:
                            matched_line = target
                            st.success(f"🎯 MATCH FOUND: '{target}' in '{line_text}'")
                            break
                    
                    if matched_line:
                        # Scroll and click
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", line_element)
                        time.sleep(2)
                        
                        st.info("🖱️ Expanding line...")
                        try:
                            line_element.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", line_element)
                        
                        time.sleep(4)
                        self.take_screenshot(f"02_expanded_{matched_line}")
                        
                        # Process this line
                        odds_data = self.process_expanded_line(matched_line)
                        results[matched_line] = {
                            'full_text': line_text,
                            **odds_data
                        }
                        processed_count += 1
                        
                        # Collapse line
                        try:
                            line_element.click()
                            time.sleep(1)
                        except:
                            pass
                            
                except Exception as e:
                    st.warning(f"⚠️ Skipping line {i+1}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            st.error(f"❌ Scraping error: {str(e)}")
            return {}
    
    def process_expanded_line(self, line_name):
        """Process an expanded line to find Betano and extract odds"""
        try:
            st.info("💰 Searching for Betano...")
            
            # Find Betano with multiple strategies
            betano_selectors = [
                '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]',
                '//a[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]',
                '//span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]'
            ]
            
            betano_element = None
            for selector in betano_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if "betano" in elem.text.lower():
                            betano_element = elem
                            st.success("✅ Found Betano!")
                            break
                    if betano_element:
                        break
                except:
                    continue
            
            if not betano_element:
                return {'over_open': 'N/A', 'over_close': 'N/A', 'under_open': 'N/A', 'under_close': 'N/A', 'error': 'Betano not found'}
            
            # Find clickable elements in Betano row
            betano_row = betano_element.find_element(By.XPATH, './ancestor::div[1]')
            buttons = betano_row.find_elements(By.XPATH, './/*[@onclick or contains(@class, "cursor-pointer") or contains(@class, "button") or contains(@class, "btn")]')
            
            st.info(f"🔘 Found {len(buttons)} clickable elements")
            
            odds_data = {
                'over_open': 'N/A', 
                'over_close': 'N/A',
                'under_open': 'N/A',
                'under_close': 'N/A'
            }
            
            # Try to click buttons and get odds
            for i, button in enumerate(buttons[:2]):  # Try first two buttons
                try:
                    button_type = "Over" if i == 0 else "Under"
                    st.info(f"🎯 Clicking {button_type} button...")
                    
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    self.take_screenshot(f"03_{button_type.lower()}_popup")
                    
                    open_odds, close_odds = self.extract_popup_odds()
                    
                    if i == 0:  # Over
                        odds_data['over_open'] = open_odds
                        odds_data['over_close'] = close_odds
                    else:  # Under
                        odds_data['under_open'] = open_odds
                        odds_data['under_close'] = close_odds
                    
                    # Close popup
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                    time.sleep(2)
                    
                except Exception as e:
                    st.warning(f"⚠️ {button_type} button failed: {e}")
            
            return odds_data
            
        except Exception as e:
            st.error(f"❌ Line processing failed: {str(e)}")
            return {'over_open': 'N/A', 'over_close': 'N/A', 'under_open': 'N/A', 'under_close': 'N/A', 'error': str(e)}
    
    def extract_popup_odds(self):
        """Extract odds from popup"""
        open_odds, close_odds = "N/A", "N/A"
        
        try:
            # Look for odds elements
            odds_elements = self.driver.find_elements(By.XPATH, '//*[contains(text(), ".")]')  # Look for decimal numbers
            
            for elem in odds_elements:
                text = elem.text.strip()
                if text and any(char.isdigit() for char in text) and '.' in text:
                    if open_odds == "N/A":
                        open_odds = text
                        st.success(f"📈 Found odds: {text}")
                    elif close_odds == "N/A":
                        close_odds = text
                        st.success(f"📉 Found odds: {text}")
                        break
                        
        except Exception as e:
            st.warning(f"⚠️ Odds extraction failed: {e}")
        
        return open_odds, close_odds
    
    def close(self):
        """Close driver"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    st.title("🎯 OddsPortal Cloud Scraper")
    
    st.info("""
    **This version should work on Streamlit Cloud!**
    - Uses undetected_chromedriver (more reliable)
    - Multiple fallback strategies
    - Handles dynamic content
    """)
    
    # Input section
    url = st.text_input("🔗 OddsPortal URL:", 
                       value="https://www.oddsportal.com/basketball/usa/nba/",
                       placeholder="Paste OddsPortal URL here")
    
    lines_input = st.text_input("📝 Lines to scrape:",
                               value="+2.5, +3.5, +4.5",
                               placeholder="Enter line values like +2.5, +3.5")
    
    if st.button("🚀 Start Scraping"):
        if url and lines_input:
            lines = [line.strip() for line in lines_input.split(",")]
            
            st.info(f"🎯 Target lines: {lines}")
            
            # Initialize scraper
            try:
                scraper = OddsScraper(debug=True)
            except Exception as e:
                st.error(f"❌ Failed to initialize scraper: {e}")
                st.info("💡 Try adding 'undetected-chromedriver' to requirements.txt")
                return
            
            # Start scraping
            try:
                with st.spinner("🕒 Scraping... This may take 1-2 minutes..."):
                    results = scraper.scrape_over_under_odds(url, lines)
                
                if results:
                    st.success(f"✅ Scraped {len(results)} lines!")
                    
                    # Display results
                    data = []
                    for line_name, odds_data in results.items():
                        data.append({
                            'Line': line_name,
                            'Full Text': odds_data.get('full_text', ''),
                            'Over Open': odds_data.get('over_open', 'N/A'),
                            'Over Close': odds_data.get('over_close', 'N/A'),
                            'Under Open': odds_data.get('under_open', 'N/A'),
                            'Under Close': odds_data.get('under_close', 'N/A')
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    
                    # Download
                    json_data = json.dumps(results, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name="odds_data.json",
                        mime="application/json"
                    )
                else:
                    st.error("❌ No results found. Check the URL and try different line values.")
                    
            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
            finally:
                scraper.close()
        else:
            st.warning("⚠️ Please enter both URL and lines.")

if __name__ == "__main__":
    main()
