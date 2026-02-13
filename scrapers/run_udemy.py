"""
Exécuter le Scraper Udemy - Sujets Multiples

Scrape des cours de plusieurs sujets et enregistre tout dans raw_udemy.json
Modifiez la liste SEARCH_QUERIES pour personnaliser les sujets.
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

# Configuration - Sujets Multiples
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

COURSES_PER_TOPIC = 70  # Nombre de cours à extraire par sujet
HEADLESS = False  # Mettre à True pour masquer la fenêtre du navigateur

async def main():
    print("="*70)
    print("="*70)
    print(" SCRAPER UDEMY - SUJETS MULTIPLES ".center(70))
    print("="*70)
    print(f"\nSujets : {len(SEARCH_QUERIES)}")
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"  {i}. {query}")
    print(f"\nCours par sujet : {COURSES_PER_TOPIC}")
    print(f"Mode sans tête (Headless) : {HEADLESS}")
    print(f"Objectif total : {len(SEARCH_QUERIES) * COURSES_PER_TOPIC} cours\n")
    
    scraper = UdemyScraper(headless=HEADLESS)
    all_courses = []
    
    try:
        await scraper.start()
        
        # Scraper chaque sujet
        for i, query in enumerate(SEARCH_QUERIES, 1):
            print("\n" + "="*70)
            print(f" SUJET {i}/{len(SEARCH_QUERIES)}: {query.upper()} ".center(70))
            print("="*70)
            
            courses = await scraper.search_and_scrape(query, limit=COURSES_PER_TOPIC)
            
            if courses:
                all_courses.extend(courses)
                print(f"\n[OK] {len(courses)} cours extraits pour '{query}'")
            else:
                print(f"\n[ATTENTION] Aucun cours extrait pour '{query}'")
            
            # Petit délai entre les sujets
            if i < len(SEARCH_QUERIES):
                print("\nAttente de 5 secondes avant le prochain sujet...")
                await asyncio.sleep(5)
        
        if not all_courses:
            print("\n[ERREUR] Aucun cours n'a été extrait pour aucun sujet.")
            return
        
        # Enregistrer tous les cours dans raw_udemy.json
        raw_data_dir = Path("data")  # Ajusté pour sauvegarder directement dans le dossier data/
        raw_data_dir.mkdir(exist_ok=True)
        
        output_file = raw_data_dir / "raw_udemy.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_courses, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print(" EXTRACTION TERMINÉE ".center(70))
        print("="*70)
        print(f"\n[SUCCÈS] Total cours extraits : {len(all_courses)}")
        print(f"[ENREGISTRÉ] {output_file.absolute()}")
        
        # Afficher l'aperçu
        print("\n" + "="*70)
        print(" APERÇU (3 premiers cours) ".center(70))
        print("="*70)
        for i, course in enumerate(all_courses[:3], 1):
            print(f"\n[Cours {i}]")
            print(f"  Titre :       {course['title'][:60]}")
            print(f"  Instructeur : {course['instructor']}")
            print(f"  Note :        {course['rating']} ({course.get('reviews', 'N/A')} avis)")
            print(f"  Prix :        {course['current_price']}")
            print(f"  Durée :       {course.get('duration_hours', 'N/A')} heures")
            print(f"  Niveau :      {course['level']}")
        
        if len(all_courses) > 3:
            print(f"\n... et {len(all_courses) - 3} autres cours")
    
    finally:
        await scraper.stop()
    
    print("\n[TERMINÉ] Tous les sujets ont été traités !")


if __name__ == "__main__":
    asyncio.run(main())
