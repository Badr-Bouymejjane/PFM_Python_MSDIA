
import asyncio
from playwright.async_api import async_playwright
import json
import os
import re
import argparse
from datetime import datetime

class UdemyScraper:
    def __init__(self, headless=False, timeout=60000):
        # Udemy usually requires headless=False to bypass Cloudflare
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
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-infobars"]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York"
        )
        self.page = await self.context.new_page()
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
        """
        print(f"[{query}] Starting scrape for {limit} items...")
        courses = []
        
        try:
            # Navigate to Home
            await self.page.goto("https://www.udemy.com", timeout=self.timeout, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Search
            await self.search_for_query(query)
            
            # Extract
            courses = await self.extract_results(limit, query)
            
            print(f"[{query}] Scrape complete. Found {len(courses)} courses.")
            return courses

        except Exception as e:
            print(f"[{query}] Error during scrape: {e}")
            await self.page.screenshot(path=f".tmp/debug/error_udemy_{query.replace(' ', '_')}.png")
            return []

    async def search_for_query(self, query):
        """Performs the search action."""
        try:
            search_input = self.page.locator('input[name="q"], input[type="search"]').first
            if await search_input.is_visible():
                await search_input.click()
                await search_input.fill(query)
                await self.page.keyboard.press("Enter")
                
                # Wait for any load state
                try:
                     await self.page.wait_for_load_state("networkidle", timeout=10000)
                except:
                     pass
                
                # Wait for results to be visible (h3 titles)
                await self.page.wait_for_selector('h3.ud-heading-lg', state="visible", timeout=20000)
                await asyncio.sleep(3) # Extra wait for dynamic content
            else:
                raise Exception("Search bar not found")
            
        except Exception as e:
            print(f"Search failed for '{query}': {e}")
            raise

    async def extract_results(self, limit, category):
        """Iterates through cards and extracts data."""
        results = []
        page_num = 1
        
        while len(results) < limit:
            print(f"Scraping category '{category}' - Page {page_num}...")
            
            # Grab all title locators first
            try:
                await self.page.wait_for_selector('h3.ud-heading-lg', timeout=15000)
            except:
                print("Timeout waiting for cards.")
                break

            titles_loc = self.page.locator('h3.ud-heading-lg')
            count = await titles_loc.count()
            print(f"  Found {count} potential cards on page.")
            
            if count == 0:
                break
            
            for i in range(count):
                if len(results) >= limit:
                    break
                
                title_el = titles_loc.nth(i)
                data = await self.extract_card_data(title_el, category)
                if data:
                    print(f"  -> Collected: {data['title'][:40]}...")
                    results.append(data)
            
            if len(results) >= limit:
                break
                
            # Pagination Logic
            print(f"  Collected {len(results)}/{limit}. Moving to next page...")
            try:
                # Udemy Next button usually: a[data-page="+1"] or text="Next"
                # Often inside a nav
                next_btn = self.page.locator('a[data-page="+1"], a[rel="next"], a:has-text("Next")').last
                
                if await next_btn.is_visible(): # Links don't have is_enabled property usually, just visible
                    await next_btn.scroll_into_view_if_needed()
                    await next_btn.click()
                    page_num += 1
                    
                    # Wait for network idle
                    try:
                        await self.page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        pass
                    await asyncio.sleep(5) # Extra wait for dynamic content
                else:
                    print("  Next button not found. End of pagination.")
                    break
            except Exception as e:
                print(f"  Pagination error: {e}")
                break
            
        return results

    async def extract_card_data(self, title_el, category):
        """Extracts individual card data using robust selectors."""
        try:
            title_text = await title_el.text_content()
            
            # Link
            link_el = title_el.locator("a")
            if not await link_el.count():
                return None
            link = await link_el.get_attribute("href")
            if link and link.startswith("/"):
                link = f"https://www.udemy.com{link}"
            
            # Container: Go up 4 levels as verified in testing
            # h3 > div > div > div > div.course-card-container (approx)
            card_container = title_el.locator("xpath=../../../..")
            
            # Helper to get clean text
            # inner_text is better than text_content as it preserves some spacing/linebreaks
            card_text = await card_container.inner_text() 
            
            # Instructor
            instructor = "Unknown"
            # Try specific selector first
            instructor_el = card_container.locator('span[data-purpose="safely-set-inner-html:course-card:visible-instructors"]')
            if await instructor_el.count():
                instructor = await instructor_el.text_content()
            else:
                 # Fallback: look for "Instructor" text line? difficult.
                 pass

            # Rating
            rating = "N/A"
            # Check for Rating: X.X text
            match = re.search(r"Rating:\s*(\d\.\d)", card_text)
            if match:
                rating = match.group(1)
            else:
                # Fallback to simple number logic if it appears near "out of 5"
                match = re.search(r"(\d\.\d)\s*out of 5", card_text)
                if match:
                    rating = match.group(1)

            # Reviews
            reviews = "N/A"
            # Look for "(X reviews)" or "(X ratings)" or just "(1,235)"
            # inner_text might show: "Rating: 4.5 out of 5 4.5 (1,234 reviews)"
            match = re.search(r"\((\d[\d,]*)\s*(reviews|ratings)?\)", card_text, re.IGNORECASE)
            if match:
                reviews = match.group(1)
            
            # Metadata
            metadata_str = "N/A"
            metadata_items = []
            
            # Hours
            hours = re.search(r"(\d+(\.\d+)?\s*total hours)", card_text, re.IGNORECASE)
            if hours: metadata_items.append(hours.group(1))
            
            # Lectures
            lectures = re.search(r"(\d+\s*lectures)", card_text, re.IGNORECASE)
            if lectures: metadata_items.append(lectures.group(1))
            
            # Level
            for lvl in ["Beginner", "Intermediate", "Expert", "All Levels"]:
                if lvl in card_text:
                    metadata_items.append(lvl)
                    break
            
            if metadata_items:
                metadata_str = " · ".join(metadata_items)

            return {
                "title": title_text,
                "partner": instructor,
                "rating": rating,
                "reviews": reviews,
                "metadata": metadata_str,
                "link": link,
                "category": category,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            # print(f"Card error: {e}")
            return None

# --- Main Test Execution ---
async def main():
    print("Initializing Robust Udemy Scraper...")
    output_file = "udemy_multi_category_test.json"
    
    # Configuration for the test
    categories_to_test = ["Data Science", "Business"]
    limit_per_category = 5
    
    scraper = UdemyScraper(headless=False) # Must be false for Cloudflare
    all_courses = []
    
    try:
        await scraper.start()
        
        for category in categories_to_test:
            courses = await scraper.scrape_category(category, limit=limit_per_category)
            all_courses.extend(courses)
            print(f"Completed {category}: {len(courses)} courses collected.")
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
