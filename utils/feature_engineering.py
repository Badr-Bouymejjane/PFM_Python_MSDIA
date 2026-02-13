"""
Ingénierie des Caractéristiques (Feature Engineering) - Créer des features pour la recommandation ML
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
    from config import CLEAN_DATA_PATH, TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE
except ImportError:
    CLEAN_DATA_PATH = 'data/courses_clean.csv'
    TFIDF_MAX_FEATURES = 5000
    TFIDF_NGRAM_RANGE = (1, 2)


class FeatureEngineer:
    """Classe pour créer les features ML"""
    
    # Stopwords français et anglais
    STOPWORDS = set([
        # Anglais
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what',
        'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
        'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
        'only', 'same', 'so', 'than', 'too', 'very', 'just', 'about', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'course', 'learn', 'learning',
        'complete', 'introduction', 'guide', 'tutorial', 'masterclass',
        
        # Français
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais',
        'dans', 'sur', 'à', 'pour', 'avec', 'par', 'ce', 'cette', 'ces',
        'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'être', 'avoir',
        'que', 'qui', 'quoi', 'dont', 'où', 'si', 'ne', 'pas', 'plus',
        'cours', 'apprendre', 'introduction', 'guide', 'tutoriel',
    ])
    
    def __init__(self, df=None):
        self.df = df if df is not None else pd.DataFrame()
        
    def load_data(self, filepath):
        """Charge les données depuis un fichier CSV"""
        print(f"📂 Chargement: {filepath}")
        self.df = pd.read_csv(filepath)
        print(f"   ✅ {len(self.df)} cours chargés")
        return self
        
    def clean_text_for_nlp(self, text):
        """Nettoie le texte pour le traitement NLP"""
        if pd.isna(text) or not isinstance(text, str):
            return ''
            
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Supprimer les caractères spéciaux
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Supprimer les chiffres isolés
        text = re.sub(r'\b\d+\b', '', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les stopwords
        words = text.split()
        words = [w for w in words if w not in self.STOPWORDS and len(w) > 2]
        
        return ' '.join(words)
        
    def create_combined_text(self):
        """Crée une colonne de texte combiné pour TF-IDF"""
        print("📝 Création du texte combiné...")
        
        text_columns = ['title', 'description', 'skills', 'category']
        
        def combine_text(row):
            parts = []
            for col in text_columns:
                if col in row and pd.notna(row[col]):
                    parts.append(str(row[col]))
            return ' '.join(parts)
            
        self.df['combined_text'] = self.df.apply(combine_text, axis=1)
        self.df['combined_text'] = self.df['combined_text'].apply(self.clean_text_for_nlp)
        
        print("   ✅ Texte combiné créé")
        return self
        
    def encode_platform(self):
        """Encode la plateforme en variable numérique"""
        print("🔢 Encodage de la plateforme...")
        
        platform_map = {
            'Coursera': 1,
            'Udemy': 2,
        }
        
        self.df['platform_encoded'] = self.df['platform'].map(platform_map).fillna(0).astype(int)
        print("   ✅ Plateforme encodée")
        return self
        
    def encode_level(self):
        """Encode le niveau en variable numérique"""
        print("🔢 Encodage du niveau...")
        
        level_map = {
            'Beginner': 1,
            'Intermediate': 2,
            'Advanced': 3,
            'All Levels': 0,
        }
        
        self.df['level_encoded'] = self.df['level'].map(level_map).fillna(0).astype(int)
        print("   ✅ Niveau encodé")
        return self
        
    def encode_price(self):
        """Encode le prix en variable numérique"""
        print("🔢 Encodage du prix...")
        
        def encode_price_value(price):
            if pd.isna(price):
                return 0
            price_str = str(price).lower()
            if 'free' in price_str:
                return 0
            elif 'subscription' in price_str:
                return 1
            else:
                # Essayer d'extraire le prix numérique
                match = re.search(r'([\d.,]+)', price_str)
                if match:
                    try:
                        return float(match.group(1).replace(',', '.'))
                    except:
                        pass
                return 2  # Paid
                
        self.df['price_encoded'] = self.df['price'].apply(encode_price_value)
        print("   ✅ Prix encodé")
        return self
        
    def normalize_rating(self):
        """Normalise le rating entre 0 et 1"""
        print("📊 Normalisation du rating...")
        
        max_rating = self.df['rating'].max() if self.df['rating'].max() > 0 else 5.0
        self.df['rating_normalized'] = self.df['rating'] / max_rating
        
        print("   ✅ Rating normalisé")
        return self
        
    def create_popularity_score(self):
        """Crée un score de popularité basé sur le rating et le nombre de reviews"""
        print("🌟 Création du score de popularité...")
        
        # Normaliser le nombre de reviews (log scale)
        self.df['reviews_log'] = np.log1p(self.df['num_reviews'].fillna(0))
        max_reviews_log = self.df['reviews_log'].max() if self.df['reviews_log'].max() > 0 else 1
        self.df['reviews_normalized'] = self.df['reviews_log'] / max_reviews_log
        
        # Score de popularité = 0.6 * rating_norm + 0.4 * reviews_norm
        self.df['popularity_score'] = (
            0.6 * self.df['rating_normalized'] +
            0.4 * self.df['reviews_normalized']
        )
        
        print("   ✅ Score de popularité créé")
        return self
        
    def create_category_encoding(self):
        """Crée un encodage one-hot des catégories"""
        print("🏷️ Encodage des catégories...")
        
        # Obtenir les catégories uniques
        categories = self.df['category'].unique()
        
        # Créer des colonnes binaires
        for cat in categories:
            col_name = f"cat_{cat.lower().replace(' ', '_')}"
            self.df[col_name] = (self.df['category'] == cat).astype(int)
            
        print(f"   ✅ {len(categories)} catégories encodées")
        return self
        
    def engineer_all(self):
        """Exécute toutes les étapes de feature engineering"""
        print("\n" + "="*60)
        print("   🔧 FEATURE ENGINEERING")
        print("="*60 + "\n")
        
        self.create_combined_text()
        self.encode_platform()
        self.encode_level()
        self.encode_price()
        self.normalize_rating()
        self.create_popularity_score()
        # self.create_category_encoding()  # Optionnel, peut créer beaucoup de colonnes
        
        print("\n✅ Feature engineering terminé")
        print(f"   📊 Colonnes créées: combined_text, platform_encoded, level_encoded,")
        print(f"      price_encoded, rating_normalized, reviews_normalized, popularity_score")
        
        return self
        
    def get_feature_columns(self):
        """Retourne les noms des colonnes de features"""
        feature_cols = [
            'platform_encoded',
            'level_encoded',
            'price_encoded',
            'rating_normalized',
            'reviews_normalized',
            'popularity_score',
        ]
        # Ajouter les colonnes de catégorie si elles existent
        cat_cols = [c for c in self.df.columns if c.startswith('cat_')]
        feature_cols.extend(cat_cols)
        
        return [c for c in feature_cols if c in self.df.columns]
        
    def save(self, filepath):
        """Sauvegarde le dataset avec les features"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {filepath}")
        return self
        
    def get_dataframe(self):
        """Retourne le DataFrame"""
        return self.df


def main():
    """Fonction principale"""
    engineer = FeatureEngineer()
    
    # Charger les données nettoyées
    try:
        engineer.load_data(CLEAN_DATA_PATH)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {CLEAN_DATA_PATH}")
        print("   Exécutez d'abord: python utils/data_cleaner.py")
        return
        
    # Engineering
    engineer.engineer_all()
    
    # Sauvegarder (écrase le fichier clean)
    engineer.save(CLEAN_DATA_PATH)
    
    # Aperçu
    print("\n📋 Colonnes de features:")
    print(engineer.get_feature_columns())
    
    print("\n📋 Aperçu du dataset:")
    print(engineer.df[['title', 'combined_text', 'popularity_score']].head(5).to_string())


if __name__ == "__main__":
    main()
