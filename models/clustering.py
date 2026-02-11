"""
Module de Clustering des Cours
Clustering K-Means pour regrouper des cours similaires
"""

import sys
import os
import io

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import json


class CourseClustering:
    """Clustering K-Means pour les cours"""
    
    def __init__(self, n_clusters=10):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.tfidf = None
        self.pca = None
        self.df = None
        self.cluster_labels = None
        self.cluster_centers_2d = None
        self.courses_2d = None
        
    def load_data(self, filepath='processed_data/final_courses_shuffled.csv'):
        """Charger les données des cours"""
        print(f"📂 Chargement des données : {filepath}")
        try:
            # Essaie d'abord avec le séparateur par défaut
            self.df = pd.read_csv(filepath)
        except:
            # Si ça échoue, essaie avec le point-virgule
            self.df = pd.read_csv(filepath, sep=';')
        
        # S'assurer que les colonnes requises sont présentes
        if 'course_id' not in self.df.columns:
            self.df['course_id'] = range(len(self.df))
        if 'instructor' not in self.df.columns and 'partner' in self.df.columns:
            self.df['instructor'] = self.df['partner']
        if 'level' not in self.df.columns and 'metadata' in self.df.columns:
            self.df['level'] = self.df['metadata'].apply(self._extract_level)
            
        print(f"   ✅ {len(self.df)} cours chargés")
        return self
        
    def _extract_level(self, metadata):
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
        
    def prepare_features(self):
        """Préparer les caractéristiques (features) pour le clustering avec une pondération optimisée et NLP"""
        print("🔧 Préparation des caractéristiques (Optimisé pour 14 clusters)...")
        
        # 1. Mots vides personnalisés (stop words) nettoyés pour garder les termes spécifiques au domaine comme 'machine' ou 'data'
        from sklearn.feature_extraction import text
        custom_stop_words = [
            'course', 'introduction', 'complete', 'specialization', 
            'professional', 'certificate', 'training', 'master', 'guide', 'weeks', 'months'
        ]
        stop_words = list(text.ENGLISH_STOP_WORDS.union(custom_stop_words))
        
        # 2. Caractéristiques pondérées : Répéter 'category' 3 fois pour lui donner la priorité
        self.df['weighted_text'] = self.df.apply(
            lambda row: (str(row['category']) + ' ') * 3 + str(row['title']),
            axis=1
        )
        
        # 3. TF-IDF avec plus de max_features (mots clés) et Bigrammes
        self.tfidf = TfidfVectorizer(
            max_features=2000, 
            stop_words=stop_words,
            ngram_range=(1, 2),
            min_df=2
        )
        tfidf_matrix = self.tfidf.fit_transform(self.df['weighted_text'])
        
        # 4. Caractéristiques numériques (optionnel, gardé pour la variété)
        numeric_features = []
        if 'rating' in self.df.columns:
            # On met à l'échelle la note pour qu'elle ne domine pas le TF-IDF
            numeric_features.append(self.df['rating'].fillna(self.df['rating'].mean()).values.reshape(-1, 1))
            
        # Combiner les caractéristiques
        if numeric_features:
            scaler = StandardScaler()
            numeric_matrix = scaler.fit_transform(np.hstack(numeric_features))
            # Diminuer le poids des caractéristiques numériques par rapport au texte (facteur 0.5)
            self.feature_matrix = np.hstack([tfidf_matrix.toarray(), numeric_matrix * 0.5])
        else:
            self.feature_matrix = tfidf_matrix.toarray()
            
        print(f"   ✅ Matrice de caractéristiques optimisée : {self.feature_matrix.shape}")
        return self
        
    def fit_clusters(self):
        """Entraîner le clustering K-Means"""
        print(f"🔮 Entraînement K-Means avec {self.n_clusters} clusters...")
        
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(self.feature_matrix)
        self.df['cluster'] = self.cluster_labels
        
        # PCA pour la visualisation 2D
        print("📊 Réduction en 2D avec PCA...")
        self.pca = PCA(n_components=2, random_state=42)
        self.courses_2d = self.pca.fit_transform(self.feature_matrix)
        self.df['x'] = self.courses_2d[:, 0]
        self.df['y'] = self.courses_2d[:, 1]
        
        # Centres des clusters en 2D
        centers_full = self.kmeans.cluster_centers_
        self.cluster_centers_2d = self.pca.transform(centers_full)
        
        print(f"   ✅ Clustering terminé")
        return self
        
    def get_cluster_info(self):
        """Obtenir des informations sur chaque cluster"""
        clusters_info = []
        
        for i in range(self.n_clusters):
            cluster_df = self.df[self.df['cluster'] == i]
            
            # Catégories principales dans le cluster
            top_categories = cluster_df['category'].value_counts().head(3).to_dict()
            
            # Statistiques moyennes
            avg_rating = cluster_df['rating'].mean() if 'rating' in cluster_df.columns else 0
            avg_duration = cluster_df['duration_hours'].mean() if 'duration_hours' in cluster_df.columns else 0
            
            # Niveau dominant
            dominant_level = cluster_df['level'].mode().iloc[0] if 'level' in cluster_df.columns and len(cluster_df) > 0 else 'All'
            
            clusters_info.append({
                'cluster_id': i,
                'count': len(cluster_df),
                'top_categories': top_categories,
                'avg_rating': round(avg_rating, 2),
                'avg_duration': round(avg_duration, 1),
                'dominant_level': dominant_level,
                'center_x': float(self.cluster_centers_2d[i, 0]),
                'center_y': float(self.cluster_centers_2d[i, 1]),
                'sample_courses': cluster_df['title'].head(5).tolist()
            })
            
        return clusters_info
        
    def get_visualization_data(self):
        """Obtenir les données pour la visualisation"""
        courses_data = []
        for _, row in self.df.iterrows():
            courses_data.append({
                'id': int(row.get('course_id', 0)),
                'title': str(row.get('title', ''))[:50],
                'category': str(row.get('category', '')),
                'cluster': int(row.get('cluster', 0)),
                'x': float(row.get('x', 0)),
                'y': float(row.get('y', 0)),
                'rating': float(row.get('rating', 0)),
                'level': str(row.get('level', 'All'))
            })
            
        centers_data = []
        for i in range(self.n_clusters):
            centers_data.append({
                'cluster_id': i,
                'x': float(self.cluster_centers_2d[i, 0]),
                'y': float(self.cluster_centers_2d[i, 1])
            })
            
        return {
            'courses': courses_data,
            'centers': centers_data,
            'clusters_info': self.get_cluster_info()
        }
        
    def get_learning_path(self, category, start_level='Beginner'):
        """Générer un parcours d'apprentissage pour une catégorie"""
        category_courses = self.df[self.df['category'].str.contains(category, case=False, na=False)]
        
        if len(category_courses) == 0:
            return []
            
        level_order = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'All Levels': 2}
        category_courses = category_courses.copy()
        category_courses['level_order'] = category_courses['level'].map(level_order).fillna(2)
        
        # Trier par niveau, puis par note
        category_courses = category_courses.sort_values(
            ['level_order', 'rating'], 
            ascending=[True, False]
        )
        
        path = []
        levels = ['Beginner', 'Intermediate', 'Advanced']
        
        for level in levels:
            level_courses = category_courses[category_courses['level'] == level]
            if len(level_courses) > 0:
                top_course = level_courses.iloc[0]
                path.append({
                    'step': len(path) + 1,
                    'level': level,
                    'course_id': int(top_course.get('course_id', 0)),
                    'title': str(top_course['title']),
                    'rating': float(top_course.get('rating', 0)),
                    'duration': float(top_course.get('duration_hours', 0)),
                    'category': category
                })
                
        return path
        
    def run(self, filepath='processed_data/final_courses_shuffled.csv'):
        """Exécuter le pipeline complet de clustering"""
        print("\n" + "="*60)
        print("   🔮 CLUSTERING DES COURS")
        print("="*60 + "\n")
        
        self.load_data(filepath)
        self.prepare_features()
        self.fit_clusters()
        
        # Afficher le résumé des clusters
        print("\n📊 Résumé des Clusters :")
        for info in self.get_cluster_info():
            cats = ', '.join(list(info['top_categories'].keys())[:2])
            print(f"   Cluster {info['cluster_id']} : {info['count']} cours ({cats})")
            
        return self


# Singleton instance
_clustering_instance = None

def get_clustering():
    global _clustering_instance
    if _clustering_instance is None:
        _clustering_instance = CourseClustering(n_clusters=14)
        _clustering_instance.run()
    return _clustering_instance


if __name__ == "__main__":
    clustering = CourseClustering(n_clusters=14)
    clustering.run()
    
    # Tester le parcours d'apprentissage
    print("\n📚 Parcours d'apprentissage : Data Science")
    path = clustering.get_learning_path("Data Science")
    for step in path:
        print(f"   {step['step']}. [{step['level']}] {step['title'][:40]}...")
