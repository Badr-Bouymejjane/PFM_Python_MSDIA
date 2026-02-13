"""
Moteur de Recommandation de Cours - Moteur de Recommandation ML
Adapté pour le jeu de données final_courses_shuffled.csv
"""

# === IMPORTATIONS ===
import sys  # Gestion du système
import os   # Gestion des fichiers

# Configuration UTF-8 pour Windows (encodage des caractères)
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bibliothèques de traitement de données
import pandas as pd  # Manipulation de données (DataFrames)
import numpy as np   # Calculs numériques (vecteurs, matrices)
import pickle  # Sauvegarde/chargement de modèles

# Bibliothèques de Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer  # Vectorisation de texte (TF-IDF)
from sklearn.metrics.pairwise import cosine_similarity  # Calcul de similarité entre cours

# === CONFIGURATION ===
# Chemin des données - utiliser final_courses_shuffled.csv
DATA_PATH = 'processed_data/final_courses_shuffled.csv'
# Paramètres TF-IDF
TFIDF_MAX_FEATURES = 5000  # Nombre maximum de mots à considérer
TFIDF_NGRAM_RANGE = (1, 2)  # Unigrammes (1 mot) et bigrammes (2 mots)
TFIDF_MIN_DF = 2  # Mot doit apparaître dans au moins 2 documents
TFIDF_MAX_DF = 0.95  # Ignorer les mots trop fréquents (>95% des documents)


# === CLASSE DE RECOMMANDATION ===
class CourseRecommender:
    """Système de recommandation de cours utilisant TF-IDF et la similarité cosinus"""
    
    def __init__(self):
        """Initialiser le système de recommandation"""
        self.df = None  # DataFrame contenant les cours
        self.tfidf_vectorizer = None  # Vectoriseur TF-IDF (texte → nombres)
        self.tfidf_matrix = None  # Matrice TF-IDF de tous les cours
        self.similarity_matrix = None  # Matrice de similarité entre tous les cours
        self.is_trained = False  # Indicateur si le modèle est entraîné
        
    def load_data(self, filepath=None):
        """Charger les données des cours depuis un fichier CSV"""
        if filepath is None:
            filepath = DATA_PATH  # Utiliser le chemin par défaut
            
        print(f"📂 Chargement des données : {filepath}")
        
        try:
            # === LECTURE DU CSV ===
            try:
                # Essayer avec le séparateur par défaut (virgule)
                self.df = pd.read_csv(filepath)
            except:
                # Si échec, essayer avec le point-virgule (format européen)
                self.df = pd.read_csv(filepath, sep=';')
            
            # === STANDARDISATION DES NOMS DE COLONNES ===
            # Mapper les anciens noms vers les nouveaux noms
            column_mapping = {
                'id': 'course_id',  # ID du cours
                'partner': 'instructor',  # Partenaire → Instructeur
                'link': 'url',  # Lien → URL
                'source_domain': 'platform',  # Domaine source → Plateforme
                'title_clean': 'combined_text'  # Titre nettoyé → Texte combiné
            }
            
            # Appliquer le mapping si les colonnes existent
            for old_col, new_col in column_mapping.items():
                if old_col in self.df.columns and new_col not in self.df.columns:
                    self.df[new_col] = self.df[old_col]
            
            # === CRÉATION DES COLONNES MANQUANTES ===
            # S'assurer que course_id existe
            if 'course_id' not in self.df.columns:
                self.df['course_id'] = range(len(self.df))  # Créer des IDs (0, 1, 2, ...)
            
            # Créer la catégorie à partir du titre si elle n'existe pas
            if 'category' not in self.df.columns:
                self.df['category'] = self.df['title'].apply(self._extract_category_from_title)
            
            # Extraire le niveau à partir des métadonnées
            if 'level' not in self.df.columns and 'metadata' in self.df.columns:
                self.df['level'] = self.df['metadata'].apply(self._extract_level)
            
            # Définir le niveau par défaut s'il n'existe pas
            if 'level' not in self.df.columns:
                self.df['level'] = 'All Levels'  # Tous niveaux par défaut
            
            # Définir le prix (Coursera = Gratuit avec abonnement)
            if 'price' not in self.df.columns:
                self.df['price'] = 'Free'  # Gratuit par défaut
            
            # Mettre le nom de la plateforme en majuscule (Coursera, Udemy)
            if 'platform' in self.df.columns:
                self.df['platform'] = self.df['platform'].str.capitalize()
                
            print(f"   ✅ {len(self.df)} cours chargés")
            return True  # Succès
        except FileNotFoundError:
            print(f"   ❌ Fichier non trouvé : {filepath}")
            return False  # Échec
    
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
        """Préparer les données pour le modèle de recommandation"""
        print("🔄 Préparation des données...")
        
        # === CRÉATION DU TEXTE COMBINÉ ===
        # Combiner titre, catégorie et niveau en un seul texte pour TF-IDF
        if 'combined_text' not in self.df.columns or self.df['combined_text'].isna().any():
            text_columns = ['title', 'category', 'level', 'partner']  # Colonnes à combiner
            # Appliquer sur chaque ligne (row)
            self.df['combined_text'] = self.df.apply(
                lambda row: ' '.join([str(row[col]) for col in text_columns if col in row.index and pd.notna(row[col])]),
                axis=1  # Appliquer sur les lignes
            )
        
        # Remplir les valeurs manquantes et convertir en minuscules
        self.df['combined_text'] = self.df['combined_text'].fillna('').str.lower()
        
        print(f"   ✅ Données préparées")
        return self  # Retourner self pour chaînage
        
    def build_tfidf_matrix(self):
        """Construire la matrice TF-IDF (convertir texte en vecteurs numériques)"""
        print("🔤 Construction de la matrice TF-IDF...")
        
        # === VECTORISATION TF-IDF ===
        # TF-IDF : mesure l'importance des mots dans chaque cours
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,  # Garder les 5000 mots les plus importants
            ngram_range=TFIDF_NGRAM_RANGE,  # Unigrammes (1 mot) et bigrammes (2 mots)
            min_df=TFIDF_MIN_DF,  # Mot doit apparaître dans au moins 2 cours
            max_df=TFIDF_MAX_DF,  # Ignorer les mots trop fréquents (>90%)
            stop_words='english'  # Ignorer les mots vides anglais (the, is, a, etc.)
        )
        
        # fit_transform : apprendre le vocabulaire et transformer en matrice
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.df['combined_text'])
        
        print(f"   📊 Vocabulaire : {len(self.tfidf_vectorizer.vocabulary_)} termes")
        print(f"   📊 Matrice TF-IDF : {self.tfidf_matrix.shape}")
        
        return self  # Retourner self pour chaînage
        
    def compute_similarity_matrix(self):
        """Calculer la matrice de similarité cosinus entre tous les cours"""
        print("🔗 Calcul de la matrice de similarité...")
        
        # === SIMILARITÉ COSINUS ===
        # Mesure la similarité entre chaque paire de cours (0 = différent, 1 = identique)
        # Chaque cellule [i,j] = similarité entre le cours i et le cours j
        self.similarity_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        
        print(f"   📊 Matrice de similarité : {self.similarity_matrix.shape}")
        
        return self  # Retourner self pour chaînage
        
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
        """Recommander des cours similaires à un cours donné"""
        # Vérifier si le modèle est entraîné
        if not self.is_trained:
            return []  # Retourner liste vide si pas entraîné
            
        # === TROUVER L'INDEX DU COURS ===
        idx = self.get_course_index(course_id)
        if idx is None or idx >= len(self.similarity_matrix):
            return []  # Cours non trouvé
            
        # === CALCULER LES SCORES DE SIMILARITÉ ===
        # enumerate : obtenir (index, score) pour chaque cours
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        # Trier par score de similarité (décroissant)
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        # Exclure le cours lui-même et garder les n meilleurs
        sim_scores = [s for s in sim_scores if s[0] != idx][:n]
        
        # === CRÉER LA LISTE DES RECOMMANDATIONS ===
        recommendations = []
        for i, (course_idx, score) in enumerate(sim_scores):
            # Récupérer les données du cours
            course = self.df.iloc[course_idx].to_dict()
            # Ajouter le score de similarité (en pourcentage)
            course['similarity_score'] = round(score * 100, 1)
            # Ajouter le rang (1, 2, 3, ...)
            course['rank'] = i + 1
            recommendations.append(course)
            
        return recommendations  # Retourner la liste des recommandations
        
    def recommend_by_query(self, query, n=10, filters=None):
        """Recommander des cours basés sur une requête textuelle (recherche)"""
        # Vérifier si le modèle est entraîné
        if not self.is_trained:
            return []  # Retourner liste vide si pas entraîné
            
        # === VECTORISER LA REQUÊTE ===
        # Transformer la requête en vecteur TF-IDF (même format que les cours)
        query_vector = self.tfidf_vectorizer.transform([query.lower()])
        # Calculer la similarité entre la requête et tous les cours
        sim_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # === VÉRIFICATION DE SYNCHRONISATION ===
        # S'assurer que les scores correspondent au nombre de cours
        if len(sim_scores) != len(self.df):
            print(f"⚠️ Le modèle n'est pas synchronisé avec les données ({len(sim_scores)} vs {len(self.df)}). Utilisation de scores de repli.")
            # Ajuster les scores si désynchronisé
            if len(sim_scores) < len(self.df):
                # Remplir avec des zéros si le modèle est en retard
                padded_scores = np.zeros(len(self.df))
                padded_scores[:len(sim_scores)] = sim_scores
                sim_scores = padded_scores
            else:
                # Tronquer si le modèle est en avance
                sim_scores = sim_scores[:len(self.df)]

        # === FILTRAGE ===
        results_df = self.df.copy()  # Copie du DataFrame
        results_df['similarity_score'] = sim_scores  # Ajouter les scores
        
        # Appliquer les filtres si fournis
        if filters:
            if filters.get('platform'):  # Filtrer par plateforme (Coursera, Udemy)
                results_df = results_df[results_df['platform'] == filters['platform']]
            if filters.get('category'):  # Filtrer par catégorie
                results_df = results_df[results_df['category'] == filters['category']]
            if filters.get('level'):  # Filtrer par niveau
                results_df = results_df[results_df['level'] == filters['level']]
                
        # === TRI ET SÉLECTION ===
        # Trier par score de similarité (décroissant) et garder les n meilleurs
        results_df = results_df.sort_values('similarity_score', ascending=False).head(n)
        
        # === CRÉATION DE LA LISTE DES RECOMMANDATIONS ===
        recommendations = []
        for i, (_, row) in enumerate(results_df.iterrows()):
            course = row.to_dict()  # Convertir en dictionnaire
            # Convertir le score en pourcentage
            course['similarity_score'] = round(course['similarity_score'] * 100, 1)
            course['rank'] = i + 1  # Ajouter le rang
            recommendations.append(course)
            
        return recommendations  # Retourner la liste des recommandations
        
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
