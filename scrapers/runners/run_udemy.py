"""
Run Udemy Scraper - Multiple Topics

Scrapes courses from multiple topics and saves all to raw_udemy.json
Edit SEARCH_QUERIES list to customize topics.
Run Udemy Scraper - Execute Udemy scraping for multiple topics
"""

import sys
import os
# Ajout du dossier parent (racine du projet) pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import json
import random
from pathlib import Path
from datetime import datetime

from scrapers.udemy import UdemyScraper

# Configuration du dossier de sortie
RAW_DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR.mkdir(exist_ok=True)

# Liste des sujets à scraper sur Udemy
# Ces mots-clés correspondent aux catégories ciblées
SEARCH_QUERIES = [
    'data science', 'machine learning', 'python', 'web development',
    'business', 'finance', 'marketing', 'design', 'photography',
    'music', 'health', 'fitness', 'personal development'
]

async def run_udemy_scraper():
    """Fonction principale pour lancer le scraping Udemy"""
    print("\n" + "="*70)
    print("   🚀 UDEMY SCRAPER - DATA COLLECTION")
    print("="*70)
    
    # Instanciation du scraper (mode visible pour débogage si besoin, ici headless=False pour voir)
    scraper = UdemyScraper(headless=False)
    
    try:
        # Démarrage du navigateur
        await scraper.start()
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
