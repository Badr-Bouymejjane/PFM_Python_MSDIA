"""
Course Clustering Module
K-Means clustering for grouping similar courses
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
    """K-Means clustering for courses"""
    
    def __init__(self, n_clusters=10):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.tfidf = None
        self.pca = None
        self.df = None
        self.cluster_labels = None
        self.cluster_centers_2d = None
        self.courses_2d = None
        
    def load_data(self, filepath='data/final_courses.csv'):
        """Load course data"""
        print(f"📂 Loading data: {filepath}")
        try:
            # Essaie d'abord avec le séparateur par défaut
            self.df = pd.read_csv(filepath)
        except:
            # Si ça échoue, essaie avec le point-virgule
            self.df = pd.read_csv(filepath, sep=';')
        
        # Ensure required columns
        if 'course_id' not in self.df.columns:
            self.df['course_id'] = range(len(self.df))
        if 'instructor' not in self.df.columns and 'partner' in self.df.columns:
            self.df['instructor'] = self.df['partner']
        if 'level' not in self.df.columns and 'metadata' in self.df.columns:
            self.df['level'] = self.df['metadata'].apply(self._extract_level)
            
        print(f"   ✅ {len(self.df)} courses loaded")
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
        """Prepare features for clustering"""
        print("🔧 Preparing features...")
        
        # Text features
        text_cols = ['title', 'category', 'level']
        self.df['text_features'] = self.df.apply(
            lambda row: ' '.join([str(row[c]) for c in text_cols if c in row.index and pd.notna(row[c])]),
            axis=1
        )
        
        # TF-IDF
        self.tfidf = TfidfVectorizer(max_features=500, stop_words='english')
        tfidf_matrix = self.tfidf.fit_transform(self.df['text_features'])
        
        # Numeric features
        numeric_features = []
        if 'rating' in self.df.columns:
            numeric_features.append(self.df['rating'].fillna(0).values.reshape(-1, 1))
        if 'duration_hours' in self.df.columns:
            numeric_features.append(self.df['duration_hours'].fillna(0).values.reshape(-1, 1))
        if 'popularity_score' in self.df.columns:
            numeric_features.append(self.df['popularity_score'].fillna(0).values.reshape(-1, 1))
            
        # Combine features
        if numeric_features:
            scaler = StandardScaler()
            numeric_matrix = scaler.fit_transform(np.hstack(numeric_features))
            self.feature_matrix = np.hstack([tfidf_matrix.toarray(), numeric_matrix])
        else:
            self.feature_matrix = tfidf_matrix.toarray()
            
        print(f"   ✅ Feature matrix: {self.feature_matrix.shape}")
        return self
        
    def fit_clusters(self):
        """Fit K-Means clustering"""
        print(f"🔮 Fitting K-Means with {self.n_clusters} clusters...")
        
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(self.feature_matrix)
        self.df['cluster'] = self.cluster_labels
        
        # PCA for 2D visualization
        print("📊 Reducing to 2D with PCA...")
        self.pca = PCA(n_components=2, random_state=42)
        self.courses_2d = self.pca.fit_transform(self.feature_matrix)
        self.df['x'] = self.courses_2d[:, 0]
        self.df['y'] = self.courses_2d[:, 1]
        
        # Cluster centers in 2D
        centers_full = self.kmeans.cluster_centers_
        self.cluster_centers_2d = self.pca.transform(centers_full)
        
        print(f"   ✅ Clustering complete")
        return self
        
    def get_cluster_info(self):
        """Get information about each cluster"""
        clusters_info = []
        
        for i in range(self.n_clusters):
            cluster_df = self.df[self.df['cluster'] == i]
            
            # Top categories in cluster
            top_categories = cluster_df['category'].value_counts().head(3).to_dict()
            
            # Top keywords
            cluster_text = ' '.join(cluster_df['text_features'].tolist())
            
            # Average stats
            avg_rating = cluster_df['rating'].mean() if 'rating' in cluster_df.columns else 0
            avg_duration = cluster_df['duration_hours'].mean() if 'duration_hours' in cluster_df.columns else 0
            
            # Dominant level
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
        """Get data for visualization"""
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
        """Generate learning path for a category"""
        category_courses = self.df[self.df['category'].str.contains(category, case=False, na=False)]
        
        if len(category_courses) == 0:
            return []
            
        level_order = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'All Levels': 2}
        category_courses = category_courses.copy()
        category_courses['level_order'] = category_courses['level'].map(level_order).fillna(2)
        
        # Sort by level, then by rating
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
        
    def run(self, filepath='data/final_courses.csv'):
        """Run complete clustering pipeline"""
        print("\n" + "="*60)
        print("   🔮 COURSE CLUSTERING")
        print("="*60 + "\n")
        
        self.load_data(filepath)
        self.prepare_features()
        self.fit_clusters()
        
        # Print cluster summary
        print("\n📊 Cluster Summary:")
        for info in self.get_cluster_info():
            cats = ', '.join(list(info['top_categories'].keys())[:2])
            print(f"   Cluster {info['cluster_id']}: {info['count']} courses ({cats})")
            
        return self


# Singleton instance
_clustering_instance = None

def get_clustering():
    global _clustering_instance
    if _clustering_instance is None:
        _clustering_instance = CourseClustering(n_clusters=8)
        _clustering_instance.run()
    return _clustering_instance


if __name__ == "__main__":
    clustering = CourseClustering(n_clusters=8)
    clustering.run()
    
    # Test learning path
    print("\n📚 Learning Path: Data Science")
    path = clustering.get_learning_path("Data Science")
    for step in path:
        print(f"   {step['step']}. [{step['level']}] {step['title'][:40]}...")
