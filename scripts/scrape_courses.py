
import asyncio
import os
import json
from datetime import datetime

# Import Scrapers
# Note: Ensure the tools folder is in python path or use relative imports effectively
try:
    from lib.scrape_coursera import CourseraScraper
    from lib.scrape_udemy import UdemyScraper
except ImportError:
    # Fallback if running from proper package context
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from lib.scrape_coursera import CourseraScraper
    from lib.scrape_udemy import UdemyScraper

# CONFIGURATION
COURSES_PER_CAT = 50 # Scaled up for Mass Scrape
CATEGORIES = [
    # Tech
    "Data Science", "Machine Learning", "Web Development", "Cybersecurity", "DevOps",
    # Business
    "Project Management", "Digital Marketing", "Finance", "Entrepreneurship", "Human Resources",
    # Creative
    "Graphic Design", "Photography", "Music Production", "Video Editing", "Game Design",
    # Lifestyle & Others
    "Personal Development", "Health and Fitness", "Language Learning", "Psychology", "History"
]

DATA_DIR = "data"

async def run_coursera_mass_scrape():
    print("\nXXX STARTING COURSERA MASS SCRAPE XXX\n")
    
    try:
        for idx, cat in enumerate(CATEGORIES):
            print(f"\n--- [Coursera {idx+1}/{len(CATEGORIES)}] Processing: {cat} ---")
            
            filename = f"raw_coursera_{cat.lower().replace(' ', '_')}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            if os.path.exists(filepath):
                 print(f"File exists for {cat}. SKIPPING to resume progress.")
                 continue
            
            # Initialize fresh browser for each category to avoid memory leaks/throttling
            scraper = CourseraScraper(headless=True)
            await scraper.start()
            
            try:
                data = await scraper.scrape_category(cat, limit=COURSES_PER_CAT)
                
                if data:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"Saved {len(data)} courses to {filename}")
                else:
                    print(f"No data found for {cat}")
            except Exception as cat_err:
                print(f"Error scraping {cat}: {cat_err}")
            finally:
                await scraper.stop()
            
            # Polite wait between categories
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Global Coursera Error: {e}")

async def run_udemy_mass_scrape():
    print("\nXXX STARTING UDEMY MASS SCRAPE (STEALTH) XXX\n")
    scraper = UdemyScraper(headless=False) # Must be False
    await scraper.start()
    
    try:
        for idx, cat in enumerate(CATEGORIES):
            print(f"\n--- [Udemy {idx+1}/{len(CATEGORIES)}] Processing: {cat} ---")
            
            filename = f"raw_udemy_{cat.lower().replace(' ', '_')}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            if os.path.exists(filepath):
                 print(f"File exists {cat}, but Overwriting for fresh data.")
            
            data = await scraper.scrape_category(cat, limit=COURSES_PER_CAT)
            
            if data:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"Saved {len(data)} courses to {filename}")
            else:
                print(f"No data found for {cat}")
                
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Global Udemy Error: {e}")
    finally:
        await scraper.stop()

async def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # Run sequentially to avoid resource contention
    await run_coursera_mass_scrape()
    await run_udemy_mass_scrape()
    
    print("\nALL MASS SCRAPING COMPLETED.")

if __name__ == "__main__":
    asyncio.run(main())
