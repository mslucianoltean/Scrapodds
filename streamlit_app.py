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
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.actions = webdriver.ActionChains(self.driver)
    
    def scrape_over_under_odds(self, url, lines):
        try:
            self.driver.get(url)
            time.sleep(5)
            
            results = {}
            
            # Find all line elements in Over/Under tab
            line_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "border-black-borders") and contains(@class, "hover:bg-gray-light") and contains(@class, "flex") and contains(@class, "h-9") and contains(@class, "cursor-pointer")]')
            
            for line_element in line_elements:
                try:
                    # Get the line value (like cl, m3, m2, etc.)
                    line_value_element = line_element.find_element(By.XPATH, './/span[contains(@class, "flex")]//span')
                    line_value = line_value_element.text.strip()
                    
                    # Check if this is one of the lines we're looking for
                    if line_value in lines:
                        st.info(f"Processing Over/Under line: {line_value}")
                        
                        # Click to expand the line
                        line_element.click()
                        time.sleep(2)
                        
                        # Look for Betano in the expanded section
                        try:
                            # Find Betano element
                            betano_xpath = './/a[contains(., "Betano")]'
                            betano_element = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, betano_xpath))
                            )
                            
                            # Click Betano odds for OVER
                            over_button_xpath = './/p[contains(@class, "flex")]'
                            over_buttons = line_element.find_elements(By.XPATH, over_button_xpath)
                            if len(over_buttons) >= 3:
                                over_buttons[2].click()  # Click the OVER button for Betano
                                time.sleep(2)
                                
                                # Extract OVER open odds
                                try:
                                    over_open_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]'
                                    over_open_element = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, over_open_xpath))
                                    )
                                    over_open = over_open_element.text.strip()
                                except:
                                    over_open = "N/A"
                                
                                # Extract OVER close odds
                                try:
                                    over_close_xpath = '/html/body/div[1]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[2]/div/div/div[2]/div'
                                    over_close_element = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, over_close_xpath))
                                    )
                                    over_close = over_close_element.text.strip()
                                except:
                                    over_close = "N/A"
                                
                                # Close the popup
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                                time.sleep(1)
                            
                            # Click Betano odds for UNDER
                            under_button_xpath = './/p[contains(@class, "flex")]'
                            under_buttons = line_element.find_elements(By.XPATH, under_button_xpath)
                            if len(under_buttons) >= 4:
                                under_buttons[3].click()  # Click the UNDER button for Betano
                                time.sleep(2)
                                
                                # Extract UNDER open odds
                                try:
                                    under_open_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]'
                                    under_open_element = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, under_open_xpath))
                                    )
                                    under_open = under_open_element.text.strip()
                                except:
                                    under_open = "N/A"
                                
                                # Extract UNDER close odds
                                try:
                                    under_close_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[2]/div/div/div[2]/div'
                                    under_close_element = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, under_close_xpath))
                                    )
                                    under_close = under_close_element.text.strip()
                                except:
                                    under_close = "N/A"
                                
                                # Close the popup
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                                time.sleep(1)
                            
                            # Store results
                            results[line_value] = {
                                'over_open': over_open,
                                'over_close': over_close,
                                'under_open': under_open,
                                'under_close': under_close
                            }
                            
                        except Exception as e:
                            st.warning(f"Could not find Betano for line {line_value}: {str(e)}")
                            continue
                            
                except Exception as e:
                    st.warning(f"Error processing line {line_value}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            st.error(f"Error scraping Over/Under: {str(e)}")
            return {}
    
    def scrape_handicap_odds(self, url, handicap_lines):
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Click handicap tab
            handicap_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[1]/div[1]/ul/li[4]/a/div'
            handicap_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, handicap_xpath))
            )
            handicap_tab.click()
            time.sleep(3)
            
            results = {}
            
            # Find all line elements in Handicap tab
            line_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "border-black-borders") and contains(@class, "hover:bg-gray-light") and contains(@class, "flex") and contains(@class, "h-9") and contains(@class, "cursor-pointer")]')
            
            for line_element in line_elements:
                try:
                    # Get the line value (like hcl, hm3, hm2, etc.)
                    line_value_element = line_element.find_element(By.XPATH, './/span[contains(@class, "flex")]//span')
                    line_value = line_value_element.text.strip()
                    
                    # Check if this is one of the handicap lines we're looking for
                    if line_value in handicap_lines:
                        st.info(f"Processing Handicap line: {line_value}")
                        
                        # Click to expand the line
                        line_element.click()
                        time.sleep(2)
                        
                        # Look for Betano in the expanded section
                        try:
                            # Find Betano element
                            betano_xpath = './/a[contains(., "Betano")]'
                            betano_element = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, betano_xpath))
                            )
                            
                            # Click Betano odds for GUEST
                            guest_button_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                            guest_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, guest_button_xpath))
                            )
                            guest_button.click()
                            time.sleep(2)
                            
                            # Extract GUEST open odds
                            try:
                                guest_open_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                                guest_open_element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, guest_open_xpath))
                                )
                                guest_open = guest_open_element.text.strip()
                            except:
                                guest_open = "N/A"
                            
                            # Extract GUEST close odds
                            try:
                                guest_close_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                                guest_close_element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, guest_close_xpath))
                                )
                                guest_close = guest_close_element.text.strip()
                            except:
                                guest_close = "N/A"
                            
                            # Close the popup
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                            time.sleep(1)
                            
                            # Click Betano odds for AWAY
                            away_button_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                            away_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, away_button_xpath))
                            )
                            away_button.click()
                            time.sleep(2)
                            
                            # Extract AWAY open odds
                            try:
                                away_open_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                                away_open_element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, away_open_xpath))
                                )
                                away_open = away_open_element.text.strip()
                            except:
                                away_open = "N/A"
                            
                            # Extract AWAY close odds
                            try:
                                away_close_xpath = '//*[@id="app"]/div[1]/div[1]/div/main/div[4]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/div/div/p'
                                away_close_element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, away_close_xpath))
                                )
                                away_close = away_close_element.text.strip()
                            except:
                                away_close = "N/A"
                            
                            # Close the popup
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys('Escape')
                            time.sleep(1)
                            
                            # Store handicap results
                            results[line_value] = {
                                'guest_open': guest_open,
                                'guest_close': guest_close,
                                'away_open': away_open,
                                'away_close': away_close
                            }
                            
                        except Exception as e:
                            st.warning(f"Could not find Betano for handicap line {line_value}: {str(e)}")
                            continue
                            
                except Exception as e:
                    st.warning(f"Error processing handicap line {line_value}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            st.error(f"Error scraping Handicap: {str(e)}")
            return {}
    
    def close(self):
        self.driver.quit()

def main():
    st.title("OddsPortal Advanced Odds Scraper")
    
    # Input section
    url = st.text_input("Enter OddsPortal URL:", placeholder="https://www.oddsportal.com/...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_under_lines = st.text_input("Over/Under Lines (comma-separated):", placeholder="cl, m3, m2, m1, p1, p2, p3")
    
    with col2:
        handicap_lines = st.text_input("Handicap Lines (comma-separated):", placeholder="hcl, hm3, hm2, hm1, hp1, hp2, hp3")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scrape_over_under = st.button("Scrape Over/Under Odds")
    
    with col2:
        scrape_handicap = st.button("Scrape Handicap Odds")
    
    with col3:
        scrape_both = st.button("Scrape Both")
    
    if (scrape_over_under or scrape_both) and url and over_under_lines:
        lines = [line.strip() for line in over_under_lines.split(",")]
        
        with st.spinner("Scraping Over/Under odds..."):
            scraper = OddsScraper()
            try:
                over_under_results = scraper.scrape_over_under_odds(url, lines)
                
                if over_under_results:
                    st.success("Successfully scraped Over/Under odds!")
                    
                    # Create DataFrame for display
                    data = []
                    for line, odds_data in over_under_results.items():
                        data.append({
                            'Line': line,
                            'Over Open': odds_data.get('over_open', 'N/A'),
                            'Over Close': odds_data.get('over_close', 'N/A'),
                            'Under Open': odds_data.get('under_open', 'N/A'),
                            'Under Close': odds_data.get('under_close', 'N/A')
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    
                    # Download JSON
                    json_data = json.dumps(over_under_results, indent=2)
                    st.download_button(
                        label="Download Over/Under JSON",
                        data=json_data,
                        file_name="over_under_odds.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No Over/Under odds found for the specified lines.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                scraper.close()
    
    if (scrape_handicap or scrape_both) and url and handicap_lines:
        lines = [line.strip() for line in handicap_lines.split(",")]
        
        with st.spinner("Scraping Handicap odds..."):
            scraper = OddsScraper()
            try:
                handicap_results = scraper.scrape_handicap_odds(url, lines)
                
                if handicap_results:
                    st.success("Successfully scraped Handicap odds!")
                    
                    # Create DataFrame for display
                    data = []
                    for line, odds_data in handicap_results.items():
                        data.append({
                            'Line': line,
                            'Guest Open': odds_data.get('guest_open', 'N/A'),
                            'Guest Close': odds_data.get('guest_close', 'N/A'),
                            'Away Open': odds_data.get('away_open', 'N/A'),
                            'Away Close': odds_data.get('away_close', 'N/A')
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    
                    # Download JSON
                    json_data = json.dumps(handicap_results, indent=2)
                    st.download_button(
                        label="Download Handicap JSON",
                        data=json_data,
                        file_name="handicap_odds.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No Handicap odds found for the specified lines.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                scraper.close()
    
    if scrape_both and url and over_under_lines and handicap_lines:
        # Combine results
        all_results = {
            "over_under": over_under_results if 'over_under_results' in locals() else {},
            "handicap": handicap_results if 'handicap_results' in locals() else {}
        }
        
        if all_results["over_under"] or all_results["handicap"]:
            st.success("Scraping completed!")
            
            # Download combined JSON
            json_data = json.dumps(all_results, indent=2)
            st.download_button(
                label="Download All Results JSON",
                data=json_data,
                file_name="all_odds_results.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
         
      
