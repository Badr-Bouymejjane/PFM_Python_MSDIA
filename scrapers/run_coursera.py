"""
Run All Scrapers - Execute Coursera and Udemy scrapers
Combines results into a single dataset
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime

from coursera_scraper import CourseraScraper

try:
    from config import CATEGORIES, MAX_COURSES_PER_CATEGORY, HEADLESS_MODE, RAW_DATA_PATH
except ImportError:
    CATEGORIES = [
        'data-science', 
        'machine-learning', 
        'python', 
        'web-development', 
        'mathematics', 
        'statistics', 
        'economics', 
        'business', 
        'finance', 
        'marketing', 
        'AI', 
        'french', 
        'english', 
        'spanish', 
        'german', 
        'physics', 
        'chemistry', 
        'biology', 
        'geology', 
        'astronomy']
    MAX_COURSES_PER_CATEGORY = 200
    HEADLESS_MODE = True
    RAW_DATA_PATH = 'data/courses_raw.csv'


async def run_coursera_scraper(categories, max_per_category):
    """Exécute le scraper Coursera"""
    scraper = CourseraScraper(headless=HEADLESS_MODE)
    courses = await scraper.scrape_all(categories, max_per_category)
    return courses








def save_combined_dataset(courses, filepath):
    """Sauvegarde le dataset combiné"""
    df = pd.DataFrame(courses)
    
    # Assurer l'ordre des colonnes
    columns_order = [
        'id', 'platform', 'title', 'description', 'category', 'skills',
        'instructor', 'rating', 'num_reviews', 'price', 'level',
        'language', 'duration', 'url', 'image_url', 'scraped_at'
    ]
    
    # Ajouter les colonnes manquantes
    for col in columns_order:
        if col not in df.columns:
            df[col] = ''
            
    # Réorganiser
    available_cols = [c for c in columns_order if c in df.columns]
    df = df[available_cols]
    
    # Sauvegarder
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8')
    
    print(f"\n💾 Dataset sauvegardé: {filepath}")
    print(f"   📊 Total: {len(df)} cours")
    print(f"   📊 Coursera: {len(df[df['platform'] == 'Coursera'])} cours")
    print(f"   📊 Udemy: {len(df[df['platform'] == 'Udemy'])} cours")
    
    return df


async def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("   🚀 COURSE RECOMMENDATION SYSTEM - DATA SCRAPING (COURSERA ONLY)")
    print("="*70)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Catégories: {len(CATEGORIES)}")
    print(f"📦 Max cours/catégorie: {MAX_COURSES_PER_CATEGORY}")
    
    # ===== COURSERA =====
    print("\n" + "-"*50)
    print("   Étape 1: Scraping Coursera")
    print("-"*50)
    
    try:
        coursera_courses = await run_coursera_scraper(CATEGORIES, MAX_COURSES_PER_CATEGORY)
    except Exception as e:
        print(f"❌ Erreur Coursera: {e}")
        coursera_courses = []
        
    if len(coursera_courses) == 0:
        print("❌ Aucun cours scrapé!")
    else:
        # Sauvegarder uniquement Coursera
        # Utiliser RAW_DATA_PATH ou un nouveau chemin
        # Pour éviter de casser la compatibilité, on sauvegarde dans coursera_raw.csv
        # ou on garde RAW_DATA_PATH en sachant qu'il n'y aura que du Coursera
        
        df = save_combined_dataset(coursera_courses, RAW_DATA_PATH)
    
    print("\n" + "="*70)
    print("   ✅ SCRAPING COURSERA TERMINÉ")
    print("="*70)
    
    return coursera_courses


if __name__ == "__main__":
    asyncio.run(main())
