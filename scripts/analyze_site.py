
import asyncio
from playwright.async_api import async_playwright

async def analyze():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test Page 1
        url1 = "https://www.coursera.org/search?query=Data%20Science"
        print(f"Visiting Page 1: {url1}")
        await page.goto(url1)
        await page.wait_for_selector('.cds-CommonCard-title', timeout=20000)
        title1 = await page.locator('.cds-CommonCard-title').first.text_content()
        print(f"Page 1 First Course: {title1}")
        
        # Test Page 2
        url2 = "https://www.coursera.org/search?query=Data%20Science&page=2"
        print(f"Visiting Page 2: {url2}")
        await page.goto(url2)
        await page.wait_for_selector('.cds-CommonCard-title', timeout=20000)
        title2 = await page.locator('.cds-CommonCard-title').first.text_content()
        print(f"Page 2 First Course: {title2}")
        
        if title1 != title2:
            print("SUCCESS: URL Pagination works! Titles are different.")
        else:
            print("FAILURE: URL Pagination ignored. Titles are same.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze())
