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
from udemy_scraper import UdemyScraper, generate_sample_udemy_data

try:
    from config import CATEGORIES, MAX_COURSES_PER_CATEGORY, HEADLESS_MODE, RAW_DATA_PATH
except ImportError:
    CATEGORIES = ['data-science', 'machine-learning', 'python', 'web-development', 'mathematics', 'statistics', 'economics', 'business', 'finance', 'marketing', 'AI', 'french', 'english', 'spanish', 'german', 'physics', 'chemistry', 'biology', 'geology', 'astronomy']
    MAX_COURSES_PER_CATEGORY = 200
    HEADLESS_MODE = True
    RAW_DATA_PATH = 'data/courses_raw.csv'


async def run_coursera_scraper(categories, max_per_category):
    """Exécute le scraper Coursera"""
    scraper = CourseraScraper(headless=HEADLESS_MODE)
    courses = await scraper.scrape_all(categories, max_per_category)
    return courses


def run_udemy_scraper(categories, max_per_category):
    """Exécute le scraper Udemy"""
    scraper = UdemyScraper()
    courses = scraper.scrape_all(categories, max_per_category)
    
    # Si peu de résultats, compléter avec des données d'exemple
    if len(courses) < len(categories) * 5:
        print("\n⚠️ Complétant avec des données d'exemple Udemy...")
        sample_courses = generate_sample_udemy_data(categories, max_per_category)
        courses.extend(sample_courses)
        
    return courses


def combine_datasets(coursera_courses, udemy_courses):
    """Combine les datasets des deux plateformes"""
    all_courses = []
    
    # Ajouter les cours Coursera
    for i, course in enumerate(coursera_courses):
        course['id'] = f"coursera_{i+1}"
        all_courses.append(course)
        
    # Ajouter les cours Udemy
    for i, course in enumerate(udemy_courses):
        course['id'] = f"udemy_{i+1}"
        all_courses.append(course)
        
    return all_courses


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
    print("   🚀 COURSE RECOMMENDATION SYSTEM - DATA SCRAPING")
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
        
    # ===== UDEMY =====
    print("\n" + "-"*50)
    print("   Étape 2: Scraping Udemy")
    print("-"*50)
    
    try:
        udemy_courses = run_udemy_scraper(CATEGORIES[:6], MAX_COURSES_PER_CATEGORY)
    except Exception as e:
        print(f"❌ Erreur Udemy: {e}")
        udemy_courses = []
        
    # ===== COMBINER =====
    print("\n" + "-"*50)
    print("   Étape 3: Combinaison des datasets")
    print("-"*50)
    
    all_courses = combine_datasets(coursera_courses, udemy_courses)
    
    if len(all_courses) == 0:
        print("❌ Aucun cours scrapé!")
        print("   Génération de données d'exemple...")
        
        # Générer des données d'exemple pour les deux plateformes
        from udemy_scraper import generate_sample_udemy_data
        udemy_sample = generate_sample_udemy_data(CATEGORIES, MAX_COURSES_PER_CATEGORY)
        
        # Créer des données Coursera similaires
        coursera_sample = []
        for i, course in enumerate(udemy_sample):
            coursera_course = course.copy()
            coursera_course['platform'] = 'Coursera'
            coursera_course['title'] = course['title'].replace('Bootcamp', 'Specialization')
            coursera_course['id'] = f"coursera_{i+1}"
            coursera_course['price'] = 'Subscription'
            coursera_sample.append(coursera_course)
            
        all_courses = udemy_sample + coursera_sample
        
    # Sauvegarder
    df = save_combined_dataset(all_courses, RAW_DATA_PATH)
    
    # Afficher un aperçu
    print("\n📊 Aperçu du dataset:")
    print(df.head(10).to_string())
    
    print("\n" + "="*70)
    print("   ✅ SCRAPING TERMINÉ")
    print("="*70)
    
    return df


if __name__ == "__main__":
    asyncio.run(main())
