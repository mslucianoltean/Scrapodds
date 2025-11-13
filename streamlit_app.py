import streamlit as st
import pandas as pd
import json
import time
import asyncio
from playwright.async_api import async_playwright
import nest_asyncio

# Apply nest_asyncio to allow running async code in Streamlit
nest_asyncio.apply()

class OddsScraper:
    def __init__(self, debug=False):
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def setup(self):
        """Setup Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
    
    async def take_screenshot(self, name):
        """Take screenshot for debugging"""
        if self.debug:
            await self.page.screenshot(path=f"{name}.png")
            st.image(f"{name}.png", caption=name, use_column_width=True)
    
    async def scrape_over_under_odds(self, url, lines):
        try:
            st.info(f"🌐 Navigating to: {url}")
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(8)
            
            await self.take_screenshot("01_page_loaded")
            
            results = {}
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Find line elements
            st.info("🔍 Searching for line elements...")
            
            line_elements = await self.page.query_selector_all('xpath=//div[contains(@class, "border-black-borders") and contains(@class, "cursor-pointer")]')
            
            if not line_elements:
                # Try alternative selector
                line_elements = await self.page.query_selector_all('div.border-black-borders')
            
            st.info(f"📊 Found {len(line_elements)} line elements")
            
            # Show what we found
            for i in range(min(5, len(line_elements))):
                try:
                    text = await line_elements[i].text_content()
                    if text and "Over/Under" in text:
                        st.info(f"Line {i+1}: '{text.strip()}'")
                except:
                    pass
            
            processed_count = 0
            max_lines = min(2, len(lines))  # Process max 2 lines
            
            for i, line_element in enumerate(line_elements):
                if processed_count >= max_lines:
                    break
                    
                try:
                    line_text = await line_element.text_content()
                    if not line_text or "Over/Under" not in line_text:
                        continue
                    
                    line_text = line_text.strip()
                    st.info(f"📝 Checking: '{line_text}'")
                    
                    # Check for matches
                    matched_line = None
                    for target in lines:
                        if target in line_text:
                            matched_line = target
                            st.success(f"🎯 MATCH FOUND: '{target}'")
                            break
                    
                    if matched_line:
                        # Scroll and click
                        await line_element.scroll_into_view_if_needed()
                        await asyncio.sleep(2)
                        
                        st.info("🖱️ Expanding line...")
                        await line_element.click()
                        await asyncio.sleep(4)
                        
                        await self.take_screenshot(f"02_expanded_{matched_line}")
                        
                        # Process this line
                        odds_data = await self.process_expanded_line(matched_line)
                        results[matched_line] = {
                            'full_text': line_text,
                            **odds_data
                        }
                        processed_count += 1
                        
                        # Click again to collapse
                        await line_element.click()
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    st.warning(f"⚠️ Skipping line {i+1}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            st.error(f"❌ Scraping error: {str(e)}")
            return {}
    
    async def process_expanded_line(self, line_name):
        """Process expanded line to find Betano"""
        try:
            st.info("💰 Searching for Betano...")
            
            # Find Betano element
            betano_element = await self.page.query_selector('xpath=//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "betano")]')
            
            if not betano_element:
                return {'over_open': 'N/A', 'over_close': 'N/A', 'under_open': 'N/A', 'under_close': 'N/A', 'error': 'Betano not found'}
            
            st.success("✅ Found Betano!")
            
            # Find Betano row and buttons
            betano_row = await betano_element.query_selector('xpath=./ancestor::div[1]')
            buttons = await betano_row.query_selector_all('xpath=.//*[@onclick or contains(@class, "cursor-pointer")]')
            
            st.info(f"🔘 Found {len(buttons)} clickable elements")
            
            odds_data = {
                'over_open': 'N/A', 
                'over_close': 'N/A',
                'under_open': 'N/A',
                'under_close': 'N/A'
            }
            
            # Click buttons and extract odds
            for i in range(min(2, len(buttons))):
                try:
                    button_type = "Over" if i == 0 else "Under"
                    st.info(f"🎯 Clicking {button_type} button...")
                    
                    await buttons[i].click()
                    await asyncio.sleep(3)
                    await self.take_screenshot(f"03_{button_type.lower()}_popup")
                    
                    open_odds, close_odds = await self.extract_popup_odds()
                    
                    if i == 0:
                        odds_data['over_open'] = open_odds
                        odds_data['over_close'] = close_odds
                    else:
                        odds_data['under_open'] = open_odds
                        odds_data['under_close'] = close_odds
                    
                    # Close popup
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    st.warning(f"⚠️ {button_type} button failed: {e}")
            
            return odds_data
            
        except Exception as e:
            st.error(f"❌ Line processing failed: {str(e)}")
            return {'over_open': 'N/A', 'over_close': 'N/A', 'under_open': 'N/A', 'under_close': 'N/A', 'error': str(e)}
    
    async def extract_popup_odds(self):
        """Extract odds from popup"""
        open_odds, close_odds = "N/A", "N/A"
        
        try:
            # Look for odds elements
            odds_elements = await self.page.query_selector_all('xpath=//*[contains(text(), ".")]')
            
            for element in odds_elements:
                text = await element.text_content()
                if text and any(char.isdigit() for char in text) and '.' in text:
                    if open_odds == "N/A":
                        open_odds = text.strip()
                        st.success(f"📈 Found odds: {open_odds}")
                    elif close_odds == "N/A":
                        close_odds = text.strip()
                        st.success(f"📉 Found odds: {close_odds}")
                        break
                        
        except Exception as e:
            st.warning(f"⚠️ Odds extraction failed: {e}")
        
        return open_odds, close_odds
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

def run_async_scraper(url, lines):
    """Run the async scraper"""
    scraper = OddsScraper(debug=True)
    
    async def main():
        await scraper.setup()
        results = await scraper.scrape_over_under_odds(url, lines)
        await scraper.close()
        return results
    
    # Run the async function
    return asyncio.run(main())

def main():
    st.title("🎯 OddsPortal Playwright Scraper")
    
    st.info("""
    **This version uses Playwright and should work on Streamlit Cloud!**
    - No ChromeDriver required
    - Better cloud compatibility
    - Fast and reliable
    """)
    
    # Input section
    url = st.text_input("🔗 OddsPortal URL:", 
                       placeholder="https://www.oddsportal.com/basketball/usa/nba/...")
    
    lines_input = st.text_input("📝 Lines to scrape:",
                               value="+2.5, +3.5",
                               placeholder="Enter line values like +2.5, +3.5")
    
    if st.button("🚀 Start Scraping"):
        if url and lines_input:
            lines = [line.strip() for line in lines_input.split(",")]
            
            st.info(f"🎯 Target lines: {lines}")
            
            try:
                with st.spinner("🕒 Scraping with Playwright... This may take 1-2 minutes..."):
                    results = run_async_scraper(url, lines)
                
                if results:
                    st.success(f"✅ Successfully scraped {len(results)} lines!")
                    
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
                    st.error("❌ No results found. Please check:")
                    st.info("1. The URL is correct and accessible")
                    st.info("2. The line values exist on the page")
                    st.info("3. Try different line values")
                    
            except Exception as e:
                st.error(f"❌ Scraping failed: {str(e)}")
                st.info("💡 If this persists, try using a different URL or contact support.")
                
        else:
            st.warning("⚠️ Please enter both URL and lines.")

if __name__ == "__main__":
    main()
