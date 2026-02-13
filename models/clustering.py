"""
Module de Clustering des Cours
Clustering K-Means pour regrouper des cours similaires
"""

# === IMPORTATIONS ===
import sys  # Gestion du système
import os   # Gestion des fichiers
import io   # Gestion des entrées/sorties

# Configuration UTF-8 pour éviter les erreurs d'encodage
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bibliothèques de traitement de données
import pandas as pd  # Manipulation de données (DataFrames)
import numpy as np   # Calculs numériques (matrices, vecteurs)

# Bibliothèques de Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer  # Vectorisation de texte (TF-IDF)
from sklearn.cluster import KMeans  # Algorithme de clustering K-Means
from sklearn.decomposition import PCA  # Réduction de dimensionnalité (visualisation 2D)
from sklearn.preprocessing import StandardScaler  # Normalisation des données
import json  # Manipulation de fichiers JSON


# === CLASSE DE CLUSTERING ===
class CourseClustering:
    """Clustering K-Means pour regrouper les cours similaires"""
    
    def __init__(self, n_clusters=24):
        """Initialiser le clustering avec le nombre de clusters souhaité"""
        self.n_clusters = n_clusters  # Nombre de groupes à créer
        self.kmeans = None  # Modèle K-Means (sera créé lors de l'entraînement)
        self.tfidf = None  # Vectoriseur TF-IDF (convertit texte en nombres)
        self.pca = None  # Réduction PCA pour visualisation 2D
        self.df = None  # DataFrame contenant les cours
        self.cluster_labels = None  # Labels des clusters pour chaque cours
        self.cluster_centers_2d = None  # Centres des clusters en 2D
        self.courses_2d = None  # Coordonnées 2D des cours
        
    def load_data(self, filepath='processed_data/final_courses_shuffled.csv'):
        """Charger les données des cours depuis un fichier CSV"""
        print(f"📂 Chargement des données : {filepath}")
        try:
            # Essayer de lire le CSV avec le séparateur par défaut (virgule)
            self.df = pd.read_csv(filepath)
        except:
            # Si échec, essayer avec le point-virgule (format européen)
            self.df = pd.read_csv(filepath, sep=';')
        
        # === VÉRIFICATION ET CRÉATION DES COLONNES MANQUANTES ===
        # Créer un ID unique pour chaque cours si absent
        if 'course_id' not in self.df.columns:
            self.df['course_id'] = range(len(self.df))  # 0, 1, 2, ...
        
        # Utiliser 'partner' comme 'instructor' si nécessaire
        if 'instructor' not in self.df.columns and 'partner' in self.df.columns:
            self.df['instructor'] = self.df['partner']
        
        # Extraire le niveau depuis les métadonnées si absent
        if 'level' not in self.df.columns and 'metadata' in self.df.columns:
            self.df['level'] = self.df['metadata'].apply(self._extract_level)
            
        print(f"   ✅ {len(self.df)} cours chargés")
        return self  # Retourner self pour permettre le chaînage de méthodes
        
    def _extract_level(self, metadata):
        """Extraire le niveau du cours depuis les métadonnées"""
        # Si pas de métadonnées, retourner niveau par défaut
        if pd.isna(metadata):
            return 'All Levels'
        
        # Convertir en minuscules pour la recherche
        metadata = str(metadata).lower()
        
        # Chercher les mots-clés de niveau
        if 'beginner' in metadata:
            return 'Beginner'  # Débutant
        elif 'intermediate' in metadata:
            return 'Intermediate'  # Intermédiaire
        elif 'advanced' in metadata:
            return 'Advanced'  # Avancé
        
        return 'All Levels'  # Par défaut : tous niveaux
        
    def prepare_features(self):
        """Préparer les caractéristiques (features) pour le clustering"""
        print("🔧 Préparation des caractéristiques (Optimisé pour 14 clusters)...")
        
        # === 1. MOTS VIDES (STOP WORDS) ===
        # Mots à ignorer car trop génériques (ex: 'course', 'introduction')
        from sklearn.feature_extraction import text
        custom_stop_words = [
            'course', 'introduction', 'complete', 'specialization', 'partner', 'instructor', 'level', 'title', 'category',
            'professional', 'certificate', 'training', 'master', 'guide', 'weeks', 'months', 'beginner', 'intermediate', 'advanced', 'all levels'
        ]
        # Combiner avec les mots vides anglais standards
        stop_words = list(text.ENGLISH_STOP_WORDS.union(custom_stop_words))
        
        # === 2. PONDÉRATION DES CARACTÉRISTIQUES ===
        # Répéter la catégorie 3 fois pour lui donner plus d'importance
        # Ex: "Data Science Data Science Data Science Python Programming"
        self.df['weighted_text'] = self.df.apply(
            lambda row: (str(row['category']) + ' ') + str(row['title']),
            axis=1  # Appliquer sur chaque ligne
        )
        
        # === 3. VECTORISATION TF-IDF ===
        # TF-IDF : convertit le texte en nombres (importance des mots)
        self.tfidf = TfidfVectorizer(
            max_features=2000,  # Garder les 2000 mots les plus importants
            stop_words=stop_words,  # Ignorer les mots vides
            ngram_range=(1, 2),  # Unigrammes (1 mot) et bigrammes (2 mots)
            min_df=2  # Mot doit apparaître dans au moins 2 documents
        )
        # fit_transform : apprendre le vocabulaire et transformer en matrice
        tfidf_matrix = self.tfidf.fit_transform(self.df['weighted_text'])
        
        # === 4. CARACTÉRISTIQUES NUMÉRIQUES ===
        # Ajouter la note (rating) comme caractéristique supplémentaire
        numeric_features = []
        if 'rating' in self.df.columns:
            # Remplir les valeurs manquantes avec la moyenne
            # reshape(-1, 1) : transformer en colonne (nécessaire pour sklearn)
            numeric_features.append(self.df['rating'].fillna(self.df['rating'].mean()).values.reshape(-1, 1))
            
        # === 5. COMBINAISON DES CARACTÉRISTIQUES ===
        if numeric_features:
            scaler = StandardScaler()  # Normaliser les valeurs numériques
            numeric_matrix = scaler.fit_transform(np.hstack(numeric_features))
            # Combiner TF-IDF et caractéristiques numériques (poids réduit à 0.5)
            # hstack : empiler horizontalement (ajouter des colonnes)
            self.feature_matrix = np.hstack([tfidf_matrix.toarray(), numeric_matrix * 0.5])
        else:
            # Si pas de caractéristiques numériques, utiliser seulement TF-IDF
            self.feature_matrix = tfidf_matrix.toarray()
            
        print(f"   ✅ Matrice de caractéristiques optimisée : {self.feature_matrix.shape}")
        return self  # Retourner self pour chaînage
        
    def fit_clusters(self):
        """Entraîner le modèle K-Means et créer les clusters"""
        print(f"🔮 Entraînement K-Means avec {self.n_clusters} clusters...")
        
        # === ENTRAÎNEMENT K-MEANS ===
        # K-Means : algorithme qui regroupe les cours similaires
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,  # Nombre de groupes à créer
            random_state=42,  # Graine aléatoire pour reproductibilité
            n_init=10  # Nombre d'initialisations (prend la meilleure)
        )
        # fit_predict : entraîner et prédire les labels en même temps
        self.cluster_labels = self.kmeans.fit_predict(self.feature_matrix)
        # Ajouter les labels au DataFrame
        self.df['cluster'] = self.cluster_labels
        
        # === RÉDUCTION PCA POUR VISUALISATION 2D ===
        # PCA : réduit les dimensions (ex: 2000 features → 2 dimensions x,y)
        print("📊 Réduction en 2D avec PCA...")
        self.pca = PCA(
            n_components=2,  # Réduire à 2 dimensions (x, y)
            random_state=42  # Reproductibilité
        )
        # Transformer tous les cours en coordonnées 2D
        self.courses_2d = self.pca.fit_transform(self.feature_matrix)
        self.df['x'] = self.courses_2d[:, 0]  # Coordonnée X
        self.df['y'] = self.courses_2d[:, 1]  # Coordonnée Y
        
        # === CENTRES DES CLUSTERS EN 2D ===
        # Transformer les centres des clusters en 2D pour visualisation
        centers_full = self.kmeans.cluster_centers_  # Centres en haute dimension
        self.cluster_centers_2d = self.pca.transform(centers_full)  # Centres en 2D
        
        print(f"   ✅ Clustering terminé")
        return self  # Retourner self pour chaînage
        
    def get_cluster_info(self):
        """Obtenir des informations détaillées sur chaque cluster"""
        clusters_info = []  # Liste pour stocker les infos de chaque cluster
        
        # Parcourir chaque cluster (0, 1, 2, ..., n_clusters-1)
        for i in range(self.n_clusters):
            # Filtrer les cours appartenant à ce cluster
            cluster_df = self.df[self.df['cluster'] == i]
            
            # === CATÉGORIES PRINCIPALES ===
            # value_counts() : compter les occurrences de chaque catégorie
            # head(3) : garder les 3 plus fréquentes
            top_categories = cluster_df['category'].value_counts().head(3).to_dict()
            
            # === STATISTIQUES MOYENNES ===
            # Calculer la note moyenne du cluster
            avg_rating = cluster_df['rating'].mean() if 'rating' in cluster_df.columns else 0
            # Calculer la durée moyenne du cluster
            avg_duration = cluster_df['duration_hours'].mean() if 'duration_hours' in cluster_df.columns else 0
            
            # === NIVEAU DOMINANT ===
            # mode() : valeur la plus fréquente (niveau le plus commun)
            dominant_level = cluster_df['level'].mode().iloc[0] if 'level' in cluster_df.columns and len(cluster_df) > 0 else 'All'
            
            # Créer le dictionnaire d'informations pour ce cluster
            clusters_info.append({
                'cluster_id': i,  # Numéro du cluster
                'count': len(cluster_df),  # Nombre de cours dans ce cluster
                'top_categories': top_categories,  # Catégories principales
                'avg_rating': round(avg_rating, 2),  # Note moyenne (2 décimales)
                'avg_duration': round(avg_duration, 1),  # Durée moyenne (1 décimale)
                'dominant_level': dominant_level,  # Niveau dominant
                'center_x': float(self.cluster_centers_2d[i, 0]),  # Position X du centre
                'center_y': float(self.cluster_centers_2d[i, 1]),  # Position Y du centre
                'sample_courses': cluster_df['title'].head(5).tolist()  # 5 exemples de cours
            })
            
        return clusters_info  # Retourner la liste des infos
        
    def get_visualization_data(self):
        """Obtenir les données pour la visualisation"""
        courses_data = []
        # Ajouter les cours au cluster
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
        # Ajouter les centres des clusters
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
        """Générer un parcours d'apprentissage progressif pour une catégorie"""
        # Filtrer les cours de la catégorie demandée (recherche insensible à la casse)
        category_courses = self.df[self.df['category'].str.contains(category, case=False, na=False)]
        
        # Si aucun cours trouvé, retourner liste vide
        if len(category_courses) == 0:
            return []
            
        # === ORDRE DES NIVEAUX ===
        # Mapper chaque niveau à un numéro pour le tri
        level_order = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'All Levels': 2 }
        category_courses = category_courses.copy()  # Copie pour éviter les warnings
        # Ajouter une colonne avec l'ordre numérique du niveau
        category_courses['level_order'] = category_courses['level'].map(level_order).fillna(2)
        
        # === TRI DES COURS ===
        # Trier par niveau (croissant), puis par note (décroissant)
        category_courses = category_courses.sort_values(
            ['level_order', 'rating'],  # Colonnes de tri
            ascending=[True, False]  # Niveau croissant, note décroissante
        )
        
        # === CRÉATION DU PARCOURS ===
        path = []  # Liste pour stocker les étapes du parcours
        levels = ['Beginner', 'Intermediate', 'Advanced']  # Ordre des niveaux
        
        # Pour chaque niveau, sélectionner le meilleur cours
        for level in levels:
            # Filtrer les cours de ce niveau
            level_courses = category_courses[category_courses['level'] == level]
            if len(level_courses) > 0:
                # Prendre le premier cours (meilleure note grâce au tri)
                top_course = level_courses.iloc[0]
                # Ajouter au parcours
                path.append({
                    'step': len(path) + 1,  # Numéro de l'étape (1, 2, 3)
                    'level': level,  # Niveau du cours
                    'course_id': int(top_course.get('course_id', 0)),  # ID du cours
                    'title': str(top_course['title']),  # Titre du cours
                    'rating': float(top_course.get('rating', 0)),  # Note du cours
                    'duration': float(top_course.get('duration_hours', 0)),  # Durée
                    'category': category  # Catégorie
                })
                
        return path  # Retourner le parcours complet
        
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
        _clustering_instance = CourseClustering(n_clusters=24)
        _clustering_instance.run()
    return _clustering_instance


if __name__ == "__main__":
    clustering = CourseClustering(n_clusters=24)
    clustering.run()
    
    # Tester le parcours d'apprentissage
    print("\n📚 Parcours d'apprentissage : Data Science")
    path = clustering.get_learning_path("Data Science")
    for step in path:
        print(f"   {step['step']}. [{step['level']}] {step['title'][:40]}...")
