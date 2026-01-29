
import asyncio
from playwright.async_api import async_playwright
import json
import os
import re
import argparse
from datetime import datetime

class CourseraScraper:
    def __init__(self, headless=True, timeout=60000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        """Initializes the browser session."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"] # Stealth measure
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        self.page = await self.context.new_page()
        
        # Anti-detection scripts
        await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def stop(self):
        """Closes the browser session."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_category(self, query, limit=10):
        """
        Scrapes courses for a specific search query.
        
        Args:
            query (str): The search term (e.g., "Data Science").
            limit (int): Maximum number of courses to extract.
            
        Returns:
            list: A list of dictionaries containing course details.
        """
        print(f"[{query}] Starting scrape for {limit} items...")
        courses = []
        
        try:
            # Navigate to Home
            await self.page.goto("https://www.coursera.org", timeout=self.timeout)
            
            # Search
            await self.search_for_query(query)
            
            # Extract
            courses = await self.extract_results(limit, query)
            
            print(f"[{query}] Scrape complete. Found {len(courses)} courses.")
            return courses

        except Exception as e:
            print(f"[{query}] Error during scrape: {e}")
            await self.page.screenshot(path=f".tmp/debug/error_{query.replace(' ', '_')}.png")
            return []

    async def search_for_query(self, query):
        """Performs the search action."""
        try:
            # Wait for any search input
            search_input = self.page.locator('input[placeholder*="learn"], input[aria-label="Search"], input[type="text"]').first
            await search_input.wait_for(state="visible", timeout=10000)
            
            await search_input.click()
            await search_input.fill(query)
            await self.page.keyboard.press("Enter")
            
            # Wait for results page to load (look for CommonCard-title)
            await self.page.wait_for_selector('li:has(.cds-CommonCard-title)', timeout=30000)
            await self.page.wait_for_load_state("networkidle")
            
        except Exception as e:
            print(f"Search failed for '{query}': {e}")
            raise

    async def extract_results(self, limit, category):
        """Iterates through pages using URL pagination."""
        results = []
        page_num = 1
        
        while len(results) < limit:
            print(f"Scraping category '{category}' - Page {page_num}...")
            
            # Construct URL with pagination
            url = f"https://www.coursera.org/search?query={category}&page={page_num}&index=prod_all_launched_products_term_optimization"
            
            try:
                if page_num > 1:
                     await self.page.goto(url, timeout=self.timeout)
                     await self.page.wait_for_load_state("networkidle")
                
                # Wait for cards
                try:
                    await self.page.wait_for_selector('li:has(.cds-CommonCard-title)', timeout=15000)
                except:
                    print("Timeout waiting for cards. Might be end of results.")
                    break

                cards = self.page.locator('li:has(.cds-CommonCard-title)')
                count = await cards.count()
                print(f"  Found {count} cards on page {page_num}.")
                
                if count == 0:
                    print("  No cards found (count=0). Stopping.")
                    break
                
                for i in range(count):
                    if len(results) >= limit:
                        break
                    
                    card = cards.nth(i)
                    data = await self.extract_card_data(card, category)
                    if data:
                        # Avoid duplicates if any
                        if not any(d['link'] == data['link'] for d in results):
                            results.append(data)
                
                print(f"  Total collected: {len(results)}/{limit}")
                
                if len(results) >= limit:
                    break
                    
                page_num += 1
                await asyncio.sleep(2) # Polite delay
                
            except Exception as e:
                print(f"  Pagination loop error: {e}")
                break
                
        return results

    async def extract_card_data(self, card, category):
        """Extracts individual card data using robust selectors."""
        try:
            # Scroll card into view
            await card.scroll_into_view_if_needed()
            
            # Title & Link
            title_el = card.locator('.cds-CommonCard-title')
            link_el = card.locator('a.cds-CommonCard-titleLink')
            
            # If standard structure isn't there, skip
            if not await title_el.count():
                return None
                
            title = await title_el.text_content()
            relative_link = await link_el.get_attribute('href')
            link = f"https://www.coursera.org{relative_link}" if relative_link else "N/A"
            
            # Partner
            partner = "Unknown"
            aria_label = await link_el.get_attribute('aria-label')
            if aria_label and "offered by" in aria_label:
                # Format: "Title, offered by Partner, Type"
                parts = aria_label.split("offered by")
                if len(parts) > 1:
                    partner = parts[1].split(",")[0].strip()
            
            # Rating
            rating = "N/A"
            # Strategy: Look for text pattern (\d\.\d) in specific rating containers
            rating_el = card.locator('div[aria-label*="Rating"], div:has-text("Rating,")').first
            if await rating_el.count():
                rating_text = await rating_el.text_content()
                match = re.search(r"(\d\.\d)", rating_text)
                if match:
                    rating = match.group(1)
            
            # Reviews
            reviews = "N/A"
            reviews_el = card.locator('text=reviews').first
            if await reviews_el.count():
                reviews = await reviews_el.text_content()
            
            # Metadata (Level, Duration, Type)
            metadata = "N/A"
            metadata_el = card.locator('.cds-CommonCard-metadata p')
            if await metadata_el.count():
                metadata = await metadata_el.text_content()
                
            return {
                "title": title,
                "partner": partner,
                "rating": rating,
                "reviews": reviews,
                "metadata": metadata,
                "link": link,
                "category": category,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Log specific card error but don't fail the batch
            # print(f"Card extraction error: {e}") 
            return None

# --- Main Test Execution ---
async def main():
    print("Initializing Robust Coursera Scraper...")
    output_file = "coursera_multi_category_test.json"
    
    # Configuration for the test
    categories_to_test = ["Data Science", "Business", "Computer Science"]
    limit_per_category = 5
    
    scraper = CourseraScraper(headless=True)
    all_courses = []
    
    try:
        await scraper.start()
        
        for category in categories_to_test:
            courses = await scraper.scrape_category(category, limit=limit_per_category)
            all_courses.extend(courses)
            print(f"Completed {category}: {len(courses)} courses collected.")
            # Brief pause between searches to be polite
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    finally:
        await scraper.stop()
        
    # Save Results
    print(f"Saving {len(all_courses)} total courses to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    if not os.path.exists(".tmp/debug"):
        os.makedirs(".tmp/debug", exist_ok=True)
    asyncio.run(main())
