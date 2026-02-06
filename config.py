"""
Configuration du système de recommandation de cours
"""

# =====================================
# SCRAPING CONFIGURATION
# =====================================

# Plateformes à scraper
PLATFORMS = ['coursera', 'udemy']

# Catégories/Domaines à scraper
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

# Mode headless pour le navigateur
HEADLESS_MODE = True

# Délai entre les requêtes (secondes)
REQUEST_DELAY = 2

# =====================================
# DATA CONFIGURATION
# =====================================

# Chemins des fichiers de données
RAW_DATA_PATH = 'data/courses_raw.csv'
CLEAN_DATA_PATH = 'data/final_courses_shuffled.csv'

# Colonnes du dataset
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
# ML CONFIGURATION
# =====================================

# Paramètres TF-IDF
TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2
TFIDF_MAX_DF = 0.95

# Nombre de recommandations par défaut
DEFAULT_RECOMMENDATIONS = 10

# =====================================
# WEB APP CONFIGURATION
# =====================================

# Flask settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Pagination
COURSES_PER_PAGE = 12

# Session
SESSION_LIFETIME_DAYS = 21
SECRET_KEY = 'course_recommender_secret_key_2024'
