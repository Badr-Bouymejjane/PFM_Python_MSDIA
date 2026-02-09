"""
Run Udemy Scraper - Multiple Topics

Scrapes courses from multiple topics and saves all to raw_udemy.json
Edit SEARCH_QUERIES list to customize topics.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.udemy_scraper import UdemyScraper

# Configuration - Multiple Topics
SEARCH_QUERIES = [
    "machine learning",
    "data science", 
    "python programming",
    "web development",
    "artificial intelligence",
    "business",
    "computer science",
    "healthcare",
]

COURSES_PER_TOPIC = 70  # Number of courses to scrape per topic
HEADLESS = False  # Set to True to hide browser window

async def main():
    print("="*70)
    print(" UDEMY SCRAPER - MULTIPLE TOPICS ".center(70))
    print("="*70)
    print(f"\nTopics: {len(SEARCH_QUERIES)}")
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"  {i}. {query}")
    print(f"\nCourses per topic: {COURSES_PER_TOPIC}")
    print(f"Headless Mode: {HEADLESS}")
    print(f"Total target: {len(SEARCH_QUERIES) * COURSES_PER_TOPIC} courses\n")
    
    scraper = UdemyScraper(headless=HEADLESS)
    all_courses = []
    
    try:
        await scraper.start()
        
        # Scrape each topic
        for i, query in enumerate(SEARCH_QUERIES, 1):
            print("\n" + "="*70)
            print(f" TOPIC {i}/{len(SEARCH_QUERIES)}: {query.upper()} ".center(70))
            print("="*70)
            
            courses = await scraper.search_and_scrape(query, limit=COURSES_PER_TOPIC)
            
            if courses:
                all_courses.extend(courses)
                print(f"\n[OK] Scraped {len(courses)} courses from '{query}'")
            else:
                print(f"\n[WARNING] No courses scraped from '{query}'")
            
            # Small delay between topics
            if i < len(SEARCH_QUERIES):
                print("\nWaiting 5 seconds before next topic...")
                await asyncio.sleep(5)
        
        if not all_courses:
            print("\n[ERROR] No courses were scraped from any topic.")
            return
        
        # Save all courses to raw_udemy.json
        raw_data_dir = Path("data")  # Adjusted to save in data/ folder directly
        raw_data_dir.mkdir(exist_ok=True)
        
        output_file = raw_data_dir / "raw_udemy.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_courses, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print(" SCRAPING COMPLETE ".center(70))
        print("="*70)
        print(f"\n[SUCCESS] Total courses scraped: {len(all_courses)}")
        print(f"[SAVED] {output_file.absolute()}")
        
        # Display preview
        print("\n" + "="*70)
        print(" PREVIEW (First 3 courses) ".center(70))
        print("="*70)
        for i, course in enumerate(all_courses[:3], 1):
            print(f"\n[Course {i}]")
            print(f"  Title:      {course['title'][:60]}")
            print(f"  Instructor: {course['instructor']}")
            print(f"  Rating:     {course['rating']} ({course.get('reviews', 'N/A')} reviews)")
            print(f"  Price:      {course['current_price']}")
            print(f"  Duration:   {course.get('duration_hours', 'N/A')} hours")
            print(f"  Level:      {course['level']}")
        
        if len(all_courses) > 3:
            print(f"\n... and {len(all_courses) - 3} more courses")
    
    finally:
        await scraper.stop()
    
    print("\n[DONE] All topics scraped!")


if __name__ == "__main__":
    asyncio.run(main())
