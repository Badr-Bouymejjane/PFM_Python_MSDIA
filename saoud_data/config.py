# Configuration pour le scraper Coursera

# ---------------------------------------
# DOMAINES À SCRAPER
# ---------------------------------------
DOMAINS = [
    "Software Engineering",
    "Mobile Development",
    "UI/UX Design",
    "Blockchain",
    "Internet of Things",
    "DevOps",
    "Game Development",
    "Graphic Design",
    "Finance",
    "Leadership"
]

# ---------------------------------------
# PARAMÈTRES DE SCRAPING
# ---------------------------------------
# Nombre maximum de cours à extraire par domaine (None = illimité)
MAX_COURSES_PER_DOMAIN = 50

# Nombre de scrolls pour charger plus de cours
NUM_SCROLLS = 5

# Pause entre les domaines (en secondes)
PAUSE_BETWEEN_DOMAINS = 5

# ---------------------------------------
# PARAMÈTRES DU NAVIGATEUR
# ---------------------------------------
# Mode headless (True = invisible, False = visible)
HEADLESS_MODE = False

# Ralentissement des actions (en ms)
SLOW_MO = 50

# Timeout pour le chargement des pages (en ms)
PAGE_TIMEOUT = 60000

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ---------------------------------------
# FICHIERS DE SORTIE
# ---------------------------------------
OUTPUT_FILE = "coursera_courses_multi_domains.csv"
JSON_OUTPUT_FILE = "coursera_courses_multi_domains.json"
SAVE_JSON = True
