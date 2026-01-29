
import asyncio
from playwright.async_api import async_playwright
import json
import os
import re

async def main():
    print("Starting Simple Coursera Scraper...")
    async with async_playwright() as p:
        # Launch browser
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        try:
            # 1. Navigate
            print("Navigating to Coursera...")
            await page.goto("https://www.coursera.org", timeout=60000)

            # 2. Search
            print("Searching for 'Data Science'...")
            search_input = page.locator('input[placeholder*="learn"], input[aria-label="Search"], input[type="text"]').first
            await search_input.wait_for(state="visible", timeout=20000)
            await search_input.click()
            await search_input.fill("Data Science")
            await page.keyboard.press("Enter")

            # 3. Wait for results
            print("Waiting for results...")
            await page.wait_for_selector('li:has(.cds-CommonCard-title)', timeout=30000)

            # 4. Extract
            cards = page.locator('li:has(.cds-CommonCard-title)')
            count = await cards.count()
            print(f"Found {count} cards. Extracting top 3...")

            courses = []
            for i in range(min(count, 3)):
                card = cards.nth(i)
                await card.scroll_into_view_if_needed()

                # Title & Link
                title_el = card.locator('.cds-CommonCard-title')
                link_el = card.locator('a.cds-CommonCard-titleLink')

                title = await title_el.text_content() if await title_el.count() else "N/A"
                relative_link = await link_el.get_attribute('href') if await link_el.count() else ""
                link = f"https://www.coursera.org{relative_link}" if relative_link else "N/A"

                # Partner (from aria-label)
                partner = "Unknown"
                if await link_el.count():
                    aria = await link_el.get_attribute('aria-label')
                    if aria and "offered by" in aria:
                        try:
                            partner = aria.split("offered by")[1].split(",")[0].strip()
                        except:
                            pass

                # Rating
                rating = "N/A"
                rating_el = card.locator('div[aria-label*="Rating"], div:has-text("Rating,")').first
                if await rating_el.count():
                    txt = await rating_el.text_content()
                    # extract 4.8 from "4.8 Star Rating" or similar
                    match = re.search(r"(\d\.\d)", txt)
                    if match:
                        rating = match.group(1)

                course_data = {
                    "title": title,
                    "partner": partner,
                    "rating": rating,
                    "link": link
                }
                courses.append(course_data)
                print(f"[{i+1}] {title} ({rating}) - {partner}")

            # 5. Save
            if not os.path.exists("data"):
                os.makedirs("data")

            with open("data/simple_coursera_test.json", "w", encoding="utf-8") as f:
                json.dump(courses, f, indent=2)
            print("Saved to data/simple_coursera_test.json")

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="error_coursera.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
