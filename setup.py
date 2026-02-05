"""
Setup Script - Initialize and run the Course Recommendation System
Handles data generation, cleaning, feature engineering, and model training
"""

import sys
import os

# Configuration UTF-8 pour Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime


def main():
    """Main setup function"""
    
    print("\n" + "="*70)
    print("   🎓 COURSE RECOMMENDATION SYSTEM - SETUP")
    print("="*70)
    print(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Generate or Scrape Data
    print("\n" + "-"*50)
    print("   Étape 1: Génération des données")
    print("-"*50)
    
    from config import RAW_DATA_PATH
    
    if os.path.exists(RAW_DATA_PATH):
        print(f"✅ Données existantes trouvées: {RAW_DATA_PATH}")
        response = input("   Voulez-vous regénérer les données? (o/n): ").strip().lower()
        if response != 'o':
            print("   → Utilisation des données existantes")
        else:
            from generate_sample_data import generate_sample_data
            generate_sample_data(500)
    else:
        print("📦 Génération des données d'exemple...")
        from generate_sample_data import generate_sample_data
        generate_sample_data(500)
    
    # Step 2: Clean Data
    print("\n" + "-"*50)
    print("   Étape 2: Nettoyage des données")
    print("-"*50)
    
    from utils.data_cleaner import DataCleaner
    from config import CLEAN_DATA_PATH
    
    cleaner = DataCleaner()
    cleaner.load_data(RAW_DATA_PATH)
    cleaner.clean_all()
    cleaner.save(CLEAN_DATA_PATH)
    
    # Step 3: Feature Engineering
    print("\n" + "-"*50)
    print("   Étape 3: Feature Engineering")
    print("-"*50)
    
    from utils.feature_engineering import FeatureEngineer
    
    engineer = FeatureEngineer()
    engineer.load_data(CLEAN_DATA_PATH)
    engineer.engineer_all()
    engineer.save(CLEAN_DATA_PATH)
    
    # Step 4: Train Model
    print("\n" + "-"*50)
    print("   Étape 4: Entraînement du modèle ML")
    print("-"*50)
    
    from models.recommender import CourseRecommender
    
    recommender = CourseRecommender()
    recommender.train(CLEAN_DATA_PATH)
    recommender.save_model()
    
    # Summary
    print("\n" + "="*70)
    print("   ✅ SETUP TERMINÉ AVEC SUCCÈS!")
    print("="*70)
    
    stats = recommender.get_stats()
    print(f"\n📊 Résumé du dataset:")
    print(f"   • Total: {stats.get('total_courses', 0)} cours")
    print(f"   • Plateformes: {list(stats.get('platforms', {}).keys())}")
    print(f"   • Catégories: {len(stats.get('categories', {}))}")
    print(f"   • Rating moyen: {stats.get('avg_rating', 0)}")
    print(f"   • Cours gratuits: {stats.get('free_courses', 0)}")
    
    print("\n🚀 Pour lancer l'application:")
    print("   python app.py")
    print(f"\n📍 Puis ouvrez: http://localhost:5000\n")


if __name__ == "__main__":
    main()
