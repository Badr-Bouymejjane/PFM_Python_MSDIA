
import asyncio
from playwright.async_api import async_playwright
import json
import os
import re

async def main():
    print("Starting Simple Udemy Scraper...")
    async with async_playwright() as p:
        # Launch browser
        # Trying headless=False to bypass Cloudflare
        headless = os.getenv("HEADLESS", "false").lower() == "true"
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-infobars"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # 1. Navigate
            print("Navigating to Udemy...")
            await page.goto("https://www.udemy.com", timeout=60000)
            await page.wait_for_load_state("domcontentloaded")

            # 2. Search
            print("Searching for 'Data Science'...")
            search_input = page.locator('input[name="q"], input[type="search"]').first
            await search_input.wait_for(state="visible", timeout=20000)
            await search_input.click()
            await search_input.fill("Data Science")
            await page.keyboard.press("Enter")

            # 3. Wait for results
            print("Waiting for results...")
            # Udemy uses h3 for titles usually
            await page.wait_for_selector('h3.ud-heading-lg', timeout=30000)

            # 4. Extract
            titles = page.locator('h3.ud-heading-lg')
            count = await titles.count()
            print(f"Found {count} cards. Extracting top 3...")

            courses = []
            for i in range(min(count, 3)):
                title_el = titles.nth(i)
                title = await title_el.text_content()

                # Link
                link_el = title_el.locator("a")
                if await link_el.count():
                    link_href = await link_el.get_attribute("href")
                else:
                    parent = title_el.locator("..")
                    link_href = await parent.get_attribute("href")

                if link_href and link_href.startswith("/"):
                    link = f"https://www.udemy.com{link_href}"
                else:
                    link = link_href or "N/A"

                # Container
                card_container = title_el.locator("xpath=../../..")
                text_content = await card_container.text_content()

                # Instructor
                instructor = "Unknown"
                # Often "Instructor: Name" is in the text
                instr_match = re.search(r"Instructor:(.+?)(?:\n|$|\d)", text_content)
                if instr_match:
                    instructor = instr_match.group(1).strip()

                # Rating - try specific selector first
                rating = "N/A"
                rating_el = card_container.locator('span[data-purpose="rating-number"], span[class*="star-rating--rating-number"]').first
                if await rating_el.count():
                    rating = await rating_el.text_content()
                else:
                    # Check for star rating container aria-label
                    star_container = card_container.locator('div[class*="star-rating"]').first
                    if await star_container.count():
                        aria = await star_container.get_attribute("aria-label")
                        if aria:
                             match = re.search(r"(\d\.\d)", aria)
                             if match:
                                 rating = match.group(1)

                    if rating == "N/A":
                        # Fallback to text search
                        match = re.search(r"Rating:\s*(\d\.\d)", text_content)
                        if not match:
                             match = re.search(r"(\d\.\d)\s*out of 5", text_content)
                        if match:
                            rating = match.group(1)

                course_data = {
                    "title": title,
                    "instructor": instructor,
                    "rating": rating,
                    "link": link
                }
                courses.append(course_data)
                print(f"[{i+1}] {title} ({rating}) - {instructor}")

            # 5. Save
            with open("data/simple_udemy_test.json", "w", encoding="utf-8") as f:
                json.dump(courses, f, indent=2)
            print("Saved to data/simple_udemy_test.json")

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="error_udemy.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
