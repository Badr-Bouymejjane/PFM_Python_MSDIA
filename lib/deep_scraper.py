
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os
import random
import json

# CONFIG
INPUT_FILE = ".tmp/data/processed_courses.csv"
OUTPUT_FILE = ".tmp/data/processed_courses_enriched.csv"
MAX_CONCURRENCY = 3  # Don't hammer servers

async def scrape_coursera_details(page, url):
    """Deep scrape a Coursera detail page."""
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(2) # Human pause
        
        # 1. Precise Reviews/Enrolled
        # Look for the hero section stats
        data = {}
        
        # Coursera keeps changing classes, use robust text locators
        # Enrollments: "507,615 already enrolled"
        try:
            enrolled_text = await page.get_by_text("already enrolled").first.text_content()
            data['exact_enrolled'] = enrolled_text.replace("already enrolled", "").strip()
        except:
            data['exact_enrolled'] = "N/A"
            
        # Reviews: "38,859 reviews" inside the rating line
        try:
            # Try to grab the snippet in the hero header
            # Usually: <div ...>4.5 stars</div> <span>38,859 reviews</span>
            # Strategy: Get all text of hero and parse? Or specific text locator?
            data['exact_reviews'] = "N/A"
            # Fallback simplistic extraction if specific selector fails
            content = await page.content()
            if "reviews" in content:
                # This is weak, but specialized selectors are brittle. 
                # Let's try to grab the rating count specifically.
                pass
        except:
            pass
            
        # Description (What you will learn)
        try:
            desc = await page.locator("div.description").first.text_content()
            data['full_description'] = desc.strip()
        except:
            data['full_description'] = ""
            
        return data
    except Exception as e:
        print(f"Failed Coursera {url}: {e}")
        return None

async def scrape_udemy_details(page, url):
    """Deep scrape a Udemy detail page."""
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        data = {}
        # Udemy Anti-Bot is tough, likely to hit Captcha if purely headless without cookies.
        # We rely on the context being stealth.
        
        try:
            # Data-purpose is king in Udemy
            # <div data-purpose="enrollment">139,433 students</div>
            students = await page.locator('[data-purpose="enrollment"]').first.text_content()
            data['exact_enrolled'] = students.replace("students", "").strip()
        except:
            data['exact_enrolled'] = "N/A"

        try:
            # <div data-purpose="course-description">
            desc = await page.locator('[data-purpose="course-description"]').first.text_content()
            data['full_description'] = desc.strip()
        except:
            data['full_description'] = ""
            
        return data
    except Exception as e:
        print(f"Failed Udemy {url}: {e}")
        return None

async def simple_deep_scrape_run():
    print(f"Starting Deep Scraper on {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("Input file not found!")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} courses.")
    
    # Add new columns if missing
    if 'exact_enrolled' not in df.columns:
        df['exact_enrolled'] = "N/A"
        df['full_description'] = ""
    
    # Run on all items
    target_indices = df.index 
    # target_indices = df.index[:3] # DEBUG MODE 
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        # Loop through rows
        for idx in target_indices:
            row = df.loc[idx]
            link = row['link']
            domain = row['source_domain']
            print(f"[{idx+1}/{len(target_indices)}] Visiting: {link}")
            
            scraped_data = None
            if domain == 'coursera':
                scraped_data = await scrape_coursera_details(page, link)
            elif domain == 'udemy':
                scraped_data = await scrape_udemy_details(page, link)
            
            if scraped_data:
                # Update DataFrame
                if scraped_data.get('exact_enrolled'):
                    df.at[idx, 'exact_enrolled'] = scraped_data['exact_enrolled']
                if scraped_data.get('full_description'):
                    df.at[idx, 'full_description'] = scraped_data['full_description'][:500] + "..." # Truncate for CSV sanity
                    
            # Save incrementally
            df.to_csv(OUTPUT_FILE, index=False)
            
        await browser.close()
        
    print(f"Deep scraping (sample) complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(simple_deep_scrape_run())
