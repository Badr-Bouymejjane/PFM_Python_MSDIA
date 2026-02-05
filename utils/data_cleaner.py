"""
Data Cleaner - Clean and preprocess the scraped course data
"""

import sys
import os

# Configuration UTF-8 pour Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import re
import string

try:
    from config import RAW_DATA_PATH, CLEAN_DATA_PATH
except ImportError:
    RAW_DATA_PATH = 'data/courses_raw.csv'
    CLEAN_DATA_PATH = 'data/courses_clean.csv'


class DataCleaner:
    """Classe pour nettoyer les données des cours"""
    
    # Mapping des catégories normalisées
    CATEGORY_MAPPING = {
        # Data Science
        'data science': 'Data Science',
        'data-science': 'Data Science',
        'data analytics': 'Data Science',
        'data analysis': 'Data Science',
        'big data': 'Data Science',
        
        # Machine Learning
        'machine learning': 'Machine Learning',
        'machine-learning': 'Machine Learning',
        'ml': 'Machine Learning',
        
        # AI
        'artificial intelligence': 'Artificial Intelligence',
        'artificial-intelligence': 'Artificial Intelligence',
        'ai': 'Artificial Intelligence',
        
        # Deep Learning
        'deep learning': 'Deep Learning',
        'deep-learning': 'Deep Learning',
        'neural networks': 'Deep Learning',
        
        # Programming
        'python': 'Python Programming',
        'python programming': 'Python Programming',
        'javascript': 'JavaScript',
        'java': 'Java Programming',
        
        # Web Development
        'web development': 'Web Development',
        'web-development': 'Web Development',
        'frontend': 'Web Development',
        'backend': 'Web Development',
        'full stack': 'Web Development',
        
        # Cloud
        'cloud computing': 'Cloud Computing',
        'cloud-computing': 'Cloud Computing',
        'aws': 'Cloud Computing',
        'azure': 'Cloud Computing',
        'gcp': 'Cloud Computing',
        
        # Security
        'cybersecurity': 'Cybersecurity',
        'cyber security': 'Cybersecurity',
        'security': 'Cybersecurity',
        
        # Business
        'business': 'Business',
        'management': 'Business',
        'entrepreneurship': 'Business',
        
        # Marketing
        'marketing': 'Marketing',
        'digital marketing': 'Marketing',
        
        # Finance
        'finance': 'Finance',
        'financial': 'Finance',
        'accounting': 'Finance',
    }
    
    # Mapping des niveaux normalisés
    LEVEL_MAPPING = {
        'beginner': 'Beginner',
        'débutant': 'Beginner',
        'introductory': 'Beginner',
        'basic': 'Beginner',
        
        'intermediate': 'Intermediate',
        'intermédiaire': 'Intermediate',
        'medium': 'Intermediate',
        
        'advanced': 'Advanced',
        'avancé': 'Advanced',
        'expert': 'Advanced',
        'professional': 'Advanced',
        
        'all levels': 'All Levels',
        'tous niveaux': 'All Levels',
        'mixed': 'All Levels',
    }
    
    def __init__(self, df=None):
        self.df = df if df is not None else pd.DataFrame()
        self.original_count = len(self.df)
        
    def load_data(self, filepath):
        """Charge les données depuis un fichier CSV"""
        print(f"📂 Chargement: {filepath}")
        self.df = pd.read_csv(filepath)
        self.original_count = len(self.df)
        print(f"   ✅ {len(self.df)} cours chargés")
        return self
        
    def remove_duplicates(self):
        """Supprime les doublons basés sur le titre"""
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['title'], keep='first')
        after = len(self.df)
        print(f"🔄 Doublons supprimés: {before - after}")
        return self
        
    def clean_text(self, text):
        """Nettoie un texte"""
        if pd.isna(text) or not isinstance(text, str):
            return ''
            
        # Supprimer les caractères spéciaux HTML
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères non-ASCII sauf accents français
        text = re.sub(r'[^\x00-\x7F\xC0-\xFF]+', ' ', text)
        
        return text.strip()
        
    def clean_titles(self):
        """Nettoie les titres des cours"""
        self.df['title'] = self.df['title'].apply(self.clean_text)
        self.df = self.df[self.df['title'].str.len() > 5]  # Titres trop courts
        print(f"✨ Titres nettoyés")
        return self
        
    def clean_descriptions(self):
        """Nettoie les descriptions des cours"""
        self.df['description'] = self.df['description'].apply(self.clean_text)
        # Remplir les descriptions vides avec le titre
        self.df['description'] = self.df.apply(
            lambda x: x['title'] if pd.isna(x['description']) or x['description'] == '' else x['description'],
            axis=1
        )
        print(f"✨ Descriptions nettoyées")
        return self
        
    def normalize_categories(self):
        """Normalise les catégories"""
        def normalize_cat(cat):
            if pd.isna(cat):
                return 'Other'
            cat_lower = str(cat).lower().strip()
            for key, value in self.CATEGORY_MAPPING.items():
                if key in cat_lower:
                    return value
            return cat.title() if isinstance(cat, str) else 'Other'
            
        self.df['category'] = self.df['category'].apply(normalize_cat)
        print(f"📁 Catégories normalisées: {self.df['category'].nunique()} catégories uniques")
        return self
        
    def normalize_levels(self):
        """Normalise les niveaux"""
        def normalize_level(level):
            if pd.isna(level):
                return 'All Levels'
            level_lower = str(level).lower().strip()
            for key, value in self.LEVEL_MAPPING.items():
                if key in level_lower:
                    return value
            return 'All Levels'
            
        self.df['level'] = self.df['level'].apply(normalize_level)
        print(f"📊 Niveaux normalisés")
        return self
        
    def clean_ratings(self):
        """Nettoie et valide les ratings"""
        def clean_rating(rating):
            if pd.isna(rating):
                return 0.0
            try:
                val = float(str(rating).replace(',', '.'))
                return min(max(val, 0.0), 5.0)  # Entre 0 et 5
            except:
                return 0.0
                
        self.df['rating'] = self.df['rating'].apply(clean_rating)
        print(f"⭐ Ratings nettoyés")
        return self
        
    def clean_num_reviews(self):
        """Nettoie le nombre de reviews"""
        def clean_reviews(num):
            if pd.isna(num):
                return 0
            try:
                text = str(num).replace(',', '').replace(' ', '')
                match = re.search(r'(\d+)', text)
                if match:
                    val = int(match.group(1))
                    if 'k' in text.lower():
                        val *= 1000
                    elif 'm' in text.lower():
                        val *= 1000000
                    return val
            except:
                pass
            return 0
            
        self.df['num_reviews'] = self.df['num_reviews'].apply(clean_reviews)
        print(f"📝 Reviews nettoyés")
        return self
        
    def clean_prices(self):
        """Normalise les prix"""
        def clean_price(price):
            if pd.isna(price):
                return 'Subscription'
            price_str = str(price).lower().strip()
            if 'free' in price_str or 'gratuit' in price_str or price_str == '0':
                return 'Free'
            elif 'subscription' in price_str or 'abonnement' in price_str:
                return 'Subscription'
            else:
                # Garder le prix original s'il contient un montant
                if re.search(r'[\d.,]+', price_str):
                    return price
                return 'Paid'
                
        self.df['price'] = self.df['price'].apply(clean_price)
        print(f"💰 Prix normalisés")
        return self
        
    def handle_missing_values(self):
        """Gère les valeurs manquantes"""
        # Colonnes avec valeurs par défaut
        defaults = {
            'platform': 'Unknown',
            'title': '',
            'description': '',
            'category': 'Other',
            'skills': '',
            'instructor': 'Unknown',
            'rating': 0.0,
            'num_reviews': 0,
            'price': 'Subscription',
            'level': 'All Levels',
            'language': 'English',
            'url': '',
        }
        
        for col, default in defaults.items():
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(default)
                
        # Supprimer les lignes sans titre
        self.df = self.df[self.df['title'].str.len() > 0]
        
        print(f"🔧 Valeurs manquantes traitées")
        return self
        
    def add_numeric_id(self):
        """Ajoute un ID numérique pour chaque cours"""
        self.df['course_id'] = range(1, len(self.df) + 1)
        print(f"🔢 IDs numériques ajoutés")
        return self
        
    def clean_all(self):
        """Exécute toutes les étapes de nettoyage"""
        print("\n" + "="*60)
        print("   🧹 NETTOYAGE DES DONNÉES")
        print("="*60 + "\n")
        
        self.remove_duplicates()
        self.clean_titles()
        self.clean_descriptions()
        self.normalize_categories()
        self.normalize_levels()
        self.clean_ratings()
        self.clean_num_reviews()
        self.clean_prices()
        self.handle_missing_values()
        self.add_numeric_id()
        
        print(f"\n✅ Nettoyage terminé:")
        print(f"   📊 Avant: {self.original_count} cours")
        print(f"   📊 Après: {len(self.df)} cours")
        print(f"   📊 Supprimés: {self.original_count - len(self.df)}")
        
        return self
        
    def get_stats(self):
        """Retourne des statistiques sur le dataset"""
        stats = {
            'total_courses': len(self.df),
            'platforms': self.df['platform'].value_counts().to_dict() if 'platform' in self.df.columns else {},
            'categories': self.df['category'].value_counts().to_dict() if 'category' in self.df.columns else {},
            'levels': self.df['level'].value_counts().to_dict() if 'level' in self.df.columns else {},
            'avg_rating': round(self.df['rating'].mean(), 2) if 'rating' in self.df.columns else 0,
            'free_courses': len(self.df[self.df['price'] == 'Free']) if 'price' in self.df.columns else 0,
        }
        return stats
        
    def save(self, filepath):
        """Sauvegarde le dataset nettoyé"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {filepath}")
        return self
        
    def get_dataframe(self):
        """Retourne le DataFrame"""
        return self.df


def main():
    """Fonction principale"""
    cleaner = DataCleaner()
    
    # Charger les données brutes
    try:
        cleaner.load_data(RAW_DATA_PATH)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {RAW_DATA_PATH}")
        print("   Exécutez d'abord: python scrapers/run_scrapers.py")
        return
        
    # Nettoyer
    cleaner.clean_all()
    
    # Statistiques
    stats = cleaner.get_stats()
    print("\n📊 Statistiques du dataset:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
        
    # Sauvegarder
    cleaner.save(CLEAN_DATA_PATH)
    
    # Aperçu
    print("\n📋 Aperçu du dataset nettoyé:")
    print(cleaner.df.head(10).to_string())


if __name__ == "__main__":
    main()
