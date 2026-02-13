"""
Configuration du système de recommandation de cours
"""

# =====================================
# CONFIGURATION DU SCRAPING
# =====================================

# Plateformes à scraper (récupérer des données)
PLATFORMS = ['coursera', 'udemy']

# Catégories/Domaines à récupérer
CATEGORIES = [
    'data-science',
    'machine-learning',
    'artificial-intelligence',
    'deep-learning',
    'python',
    'web-development',
    'javascript',
    'cloud-computing',
    'cybersecurity',
    'business',
    'marketing',
    'finance',
]

# Nombre maximum de cours par catégorie
MAX_COURSES_PER_CATEGORY = 50

# Mode "sans tête" pour le navigateur (ne pas afficher la fenêtre)
HEADLESS_MODE = True

# Délai entre les requêtes en secondes (pour éviter d'être bloqué)
REQUEST_DELAY = 2

# =====================================
# CONFIGURATION DES DONNÉES
# =====================================

# Chemins des fichiers de données
RAW_DATA_PATH = 'final_data/final_data.csv'
CLEAN_DATA_PATH = 'processed_data/final_courses_shuffled.csv'

# Colonnes du dataset (jeu de données)
DATASET_COLUMNS = [
    'id',
    'platform',
    'title',
    'description',
    'category',
    'skills',
    'instructor',
    'rating',
    'num_reviews',
    'price',
    'level',
    'language',
    'duration',
    'url',
    'image_url',
    'scraped_at'
]

# =====================================
# CONFIGURATION DU MACHINE LEARNING
# =====================================

# Paramètres TF-IDF (Analyse de texte)
TFIDF_MAX_FEATURES = 5000  # Nombre max de mots clés
TFIDF_NGRAM_RANGE = (1, 2) # Unigrammes et bigrammes
TFIDF_MIN_DF = 2           # Fréquence minimum
TFIDF_MAX_DF = 0.95        # Fréquence maximum

# Nombre de recommandations par défaut à afficher
DEFAULT_RECOMMENDATIONS = 10

# =====================================
# CONFIGURATION DE L'APPLICATION WEB
# =====================================

# Paramètres Flask (Serveur Web)
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 2400
FLASK_DEBUG = True

# Pagination (nombre de cours par page)
COURSES_PER_PAGE = 12

# Session
SESSION_LIFETIME_DAYS = 21  # Durée de vie de la session en jours
SECRET_KEY = 'course_recommender_secret_key_2024'
