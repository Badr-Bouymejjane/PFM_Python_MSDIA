"""
Moteur de Recommandation de Cours - Moteur de Recommandation ML
Adapté pour le jeu de données final_courses_shuffled.csv
"""

import sys
import os

# Configuration UTF-8 pour Windows
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Chemin des données - utiliser final_courses_shuffled.csv
DATA_PATH = 'processed_data/final_courses_shuffled.csv'
TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2
TFIDF_MAX_DF = 0.95


class CourseRecommender:
    """Système de recommandation de cours utilisant TF-IDF et la similarité cosinus"""
    
    def __init__(self):
        self.df = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.similarity_matrix = None
        self.is_trained = False
        
    def load_data(self, filepath=None):
        """Charger les données des cours"""
        if filepath is None:
            filepath = DATA_PATH
            
        print(f"📂 Chargement des données : {filepath}")
        
        try:
            # Essaie d'abord avec le séparateur par défaut
            try:
                self.df = pd.read_csv(filepath)
            except:
                # Si ça échoue, essaie avec le point-virgule
                self.df = pd.read_csv(filepath, sep=';')
            
            # Standardiser les noms de colonnes pour l'application
            column_mapping = {
                'id': 'course_id',
                'partner': 'instructor',
                'link': 'url',
                'source_domain': 'platform',
                'title_clean': 'combined_text'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in self.df.columns and new_col not in self.df.columns:
                    self.df[new_col] = self.df[old_col]
            
            # S'assurer que course_id existe
            if 'course_id' not in self.df.columns:
                self.df['course_id'] = range(len(self.df))
            
            # Créer la catégorie à partir du titre si elle n'existe pas
            if 'category' not in self.df.columns:
                self.df['category'] = self.df['title'].apply(self._extract_category_from_title)
            
            # Extraire le niveau à partir des métadonnées
            if 'level' not in self.df.columns and 'metadata' in self.df.columns:
                self.df['level'] = self.df['metadata'].apply(self._extract_level)
            
            # Définir le niveau par défaut s'il n'existe pas
            if 'level' not in self.df.columns:
                self.df['level'] = 'All Levels'
            
            # Définir le prix en fonction de la plateforme (Coursera = Gratuit avec abonnement)
            if 'price' not in self.df.columns:
                self.df['price'] = 'Free'
            
            # Mettre le nom de la plateforme en majuscule
            if 'platform' in self.df.columns:
                self.df['platform'] = self.df['platform'].str.capitalize()
                
            print(f"   ✅ {len(self.df)} cours chargés")
            return True
        except FileNotFoundError:
            print(f"   ❌ Fichier non trouvé : {filepath}")
            return False
    
    def _extract_category_from_title(self, title):
        """Extraire la catégorie du titre du cours"""
        if pd.isna(title):
            return 'General'
        
        title_lower = str(title).lower()
        
        # Dictionnaire de mots-clés pour les catégories
        categories = {
            'Data Science': ['data science', 'data analytics', 'data analysis', 'big data'],
            'Machine Learning': ['machine learning', 'ml ', 'deep learning', 'neural network'],
            'Programming': ['python', 'java', 'javascript', 'programming', 'coding', 'developer'],
            'Web Development': ['web development', 'web design', 'html', 'css', 'react', 'angular', 'vue'],
            'Business': ['business', 'management', 'marketing', 'finance', 'accounting', 'entrepreneurship'],
            'Design': ['design', 'photoshop', 'illustrator', 'ui', 'ux', 'graphic'],
            'IT & Software': ['software', 'cloud', 'aws', 'azure', 'devops', 'docker', 'kubernetes'],
            'Health & Fitness': ['health', 'fitness', 'yoga', 'nutrition', 'medical', 'healthcare'],
            'Personal Development': ['leadership', 'productivity', 'communication', 'career'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        return 'General'
    
    def _extract_level(self, metadata):
        """Extraire le niveau de la chaîne de métadonnées"""
        if pd.isna(metadata):
            return 'All Levels'
        metadata = str(metadata).lower()
        if 'beginner' in metadata:
            return 'Beginner'
        elif 'intermediate' in metadata:
            return 'Intermediate'
        elif 'advanced' in metadata:
            return 'Advanced'
        return 'All Levels'
            
    def prepare_data(self):
        """Préparer les données pour le modèle"""
        print("🔄 Préparation des données...")
        
        # Créer le texte combiné pour TF-IDF
        if 'combined_text' not in self.df.columns or self.df['combined_text'].isna().any():
            text_columns = ['title', 'category', 'level']
            self.df['combined_text'] = self.df.apply(
                lambda row: ' '.join([str(row[col]) for col in text_columns if col in row.index and pd.notna(row[col])]),
                axis=1
            )
        
        self.df['combined_text'] = self.df['combined_text'].fillna('').str.lower()
        
        print(f"   ✅ Données préparées")
        return self
        
    def build_tfidf_matrix(self):
        """Construire la matrice TF-IDF"""
        print("🔤 Construction de la matrice TF-IDF...")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,
            ngram_range=TFIDF_NGRAM_RANGE,
            min_df=TFIDF_MIN_DF,
            max_df=TFIDF_MAX_DF,
            stop_words='english'
        )
        
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.df['combined_text'])
        
        print(f"   📊 Vocabulaire : {len(self.tfidf_vectorizer.vocabulary_)} termes")
        print(f"   📊 Matrice TF-IDF : {self.tfidf_matrix.shape}")
        
        return self
        
    def compute_similarity_matrix(self):
        """Calculer la matrice de similarité cosinus"""
        print("🔗 Calcul de la matrice de similarité...")
        
        self.similarity_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        
        print(f"   📊 Matrice de similarité : {self.similarity_matrix.shape}")
        
        return self
        
    def train(self, filepath=None):
        """Entraîner le modèle de recommandation"""
        print("\n" + "="*60)
        print("   🧠 ENTRAÎNEMENT DU MODÈLE DE RECOMMANDATION")
        print("="*60 + "\n")
        
        if not self.load_data(filepath):
            return False
            
        self.prepare_data()
        self.build_tfidf_matrix()
        self.compute_similarity_matrix()
        
        self.is_trained = True
        
        print("\n✅ Modèle entraîné avec succès !")
        
        return True
        
    def get_course_by_id(self, course_id):
        """Obtenir un cours par son ID"""
        if self.df is None:
            return None
            
        if 'course_id' in self.df.columns:
            matches = self.df[self.df['course_id'] == course_id]
            if len(matches) > 0:
                return matches.iloc[0].to_dict()
                
        if course_id < len(self.df):
            return self.df.iloc[course_id].to_dict()
            
        return None
        
    def get_course_index(self, course_id):
        """Obtenir l'index du cours par son ID"""
        if 'course_id' in self.df.columns:
            matches = self.df[self.df['course_id'] == course_id]
            if len(matches) > 0:
                return matches.index[0]
        
        if course_id < len(self.df):
            return course_id
            
        return None
        
    def recommend_similar(self, course_id, n=10):
        """Recommander des cours similaires"""
        if not self.is_trained:
            return []
            
        idx = self.get_course_index(course_id)
        if idx is None or idx >= len(self.similarity_matrix):
            return []
            
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = [s for s in sim_scores if s[0] != idx][:n]
        
        recommendations = []
        for i, (course_idx, score) in enumerate(sim_scores):
            course = self.df.iloc[course_idx].to_dict()
            course['similarity_score'] = round(score * 100, 1)
            course['rank'] = i + 1
            recommendations.append(course)
            
        return recommendations
        
    def recommend_by_query(self, query, n=10, filters=None):
        """Recommander des cours basés sur une requête textuelle"""
        if not self.is_trained:
            return []
            
        query_vector = self.tfidf_vectorizer.transform([query.lower()])
        sim_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # S'assurer que les scores de similarité correspondent à la longueur du dataframe (gère les modèles désynchronisés)
        if len(sim_scores) != len(self.df):
            print(f"⚠️ Le modèle n'est pas synchronisé avec les données ({len(sim_scores)} vs {len(self.df)}). Utilisation de scores de repli.")
            # Créer un score simple basé sur la correspondance des mots-clés comme repli ou utiliser des scores partiels
            if len(sim_scores) < len(self.df):
                # Remplir avec des zéros si le modèle est en retard
                padded_scores = np.zeros(len(self.df))
                padded_scores[:len(sim_scores)] = sim_scores
                sim_scores = padded_scores
            else:
                # Tronquer si le modèle est en avance (improbable mais possible)
                sim_scores = sim_scores[:len(self.df)]

        results_df = self.df.copy()
        results_df['similarity_score'] = sim_scores
        
        if filters:
            if filters.get('platform'):
                results_df = results_df[results_df['platform'] == filters['platform']]
            if filters.get('category'):
                results_df = results_df[results_df['category'] == filters['category']]
            if filters.get('level'):
                results_df = results_df[results_df['level'] == filters['level']]
                
        results_df = results_df.sort_values('similarity_score', ascending=False).head(n)
        
        recommendations = []
        for i, (_, row) in enumerate(results_df.iterrows()):
            course = row.to_dict()
            course['similarity_score'] = round(course['similarity_score'] * 100, 1)
            course['rank'] = i + 1
            recommendations.append(course)
            
        return recommendations
        
    def get_popular_courses(self, n=10, category=None):
        """Obtenir les cours populaires"""
        if self.df is None:
            return []
            
        results_df = self.df.copy()
        
        if category:
            results_df = results_df[results_df['category'] == category]
            
        if 'popularity_score' in results_df.columns:
            results_df = results_df.sort_values('popularity_score', ascending=False)
        else:
            results_df = results_df.sort_values('rating', ascending=False)
            
        return results_df.head(n).to_dict('records')
        
    def get_all_courses(self, page=1, per_page=12, sort_by='rating', filters=None):
        """Obtenir tous les cours avec pagination"""
        if self.df is None:
            return {'courses': [], 'total': 0, 'pages': 0}
            
        results_df = self.df.copy()
        
        if filters:
            if filters.get('platform'):
                results_df = results_df[results_df['platform'] == filters['platform']]
            if filters.get('category'):
                results_df = results_df[results_df['category'] == filters['category']]
            if filters.get('level'):
                results_df = results_df[results_df['level'] == filters['level']]
            if filters.get('search'):
                search_term = filters['search'].lower()
                results_df = results_df[
                    results_df['title'].str.lower().str.contains(search_term, na=False)
                ]
                
        if sort_by in results_df.columns:
            results_df = results_df.sort_values(sort_by, ascending=False)
            
        total = len(results_df)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            'courses': results_df.iloc[start:end].to_dict('records'),
            'total': total,
            'pages': total_pages,
            'current_page': page
        }
        
    def get_categories(self):
        """Obtenir la liste des catégories"""
        if self.df is None:
            return []
        return sorted(self.df['category'].dropna().unique().tolist())
        
    def get_platforms(self):
        """Obtenir la liste des plateformes"""
        if self.df is None:
            return []
        return self.df['platform'].dropna().unique().tolist()
        
    def get_levels(self):
        """Obtenir la liste des niveaux"""
        if self.df is None:
            return []
        return self.df['level'].dropna().unique().tolist()
        
    def get_stats(self):
        """Obtenir les statistiques du jeu de données"""
        if self.df is None:
            return {}
            
        return {
            'total_courses': len(self.df),
            'platforms': self.df['platform'].value_counts().to_dict() if 'platform' in self.df.columns else {},
            'categories': self.df['category'].value_counts().to_dict() if 'category' in self.df.columns else {},
            'levels': self.df['level'].value_counts().to_dict() if 'level' in self.df.columns else {},
            'avg_rating': round(self.df['rating'].mean(), 2) if 'rating' in self.df.columns else 0,
            'free_courses': len(self.df),
        }
        
    def save_model(self, filepath='models/recommender.pkl'):
        """Sauvegarder le modèle"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'tfidf_matrix': self.tfidf_matrix,
            'similarity_matrix': self.similarity_matrix,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
            
        print(f"💾 Modèle sauvegardé : {filepath}")
        
    def load_model(self, filepath='models/recommender.pkl'):
        """Charger le modèle et vérifier la cohérence si les données sont déjà chargées"""
        try:
            if not os.path.exists(filepath):
                return False
                
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.tfidf_matrix = model_data['tfidf_matrix']
            self.similarity_matrix = model_data['similarity_matrix']
            
            # Vérifier la cohérence avec self.df s'il existe
            if self.df is not None:
                if self.tfidf_matrix.shape[0] != len(self.df):
                    print(f"⚠️ Le modèle à {filepath} n'est pas synchronisé avec les données : matrice {self.tfidf_matrix.shape[0]} lignes, CSV {len(self.df)} lignes.")
                    return False
                    
            self.is_trained = True
            print(f"📂 Modèle chargé : {filepath}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle : {e}")
            return False


if __name__ == "__main__":
    recommender = CourseRecommender()
    if recommender.train():
        recommender.save_model()
        
        # Test
        recs = recommender.recommend_by_query("python programming", n=5)
        print("\n🔍 Test: 'python programming'")
        for r in recs:
            print(f"   {r['rank']}. {r['title'][:50]}... ({r['similarity_score']}%)")
