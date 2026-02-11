import json
import re

notebook_path = r"c:\Users\LEGION 5\Desktop\SDIA - S7\Python\projet\Recommandations\notebooks\Courses_Recommandation.ipynb"

def translate_text(text):
    # Markdown translations
    replacements = {
        "# Course Recommendation System": "# Système de Recommandation de Cours",
        "This notebook demonstrates the course recommendation engine using TF-IDF and cosine similarity.": "Ce notebook démontre le moteur de recommandation de cours utilisant TF-IDF et la similarité cosinus.",
        
        # Code comments and strings
        "# Load the course data": "# Charger les données de cours",
        "Loaded {len(df)} courses": "Chargé {len(df)} cours",
        "# Check for missing values": "# Vérifier les valeurs manquantes",
        "Missing values:": "Valeurs manquantes :",
        "Dataset shape:": "Taille du jeu de données :",
        "Columns:": "Colonnes :",
        "# Prepare text for TF-IDF": "# Préparer le texte pour TF-IDF",
        "# Combine title, category, and other relevant fields": "# Combiner titre, catégorie et autres champs pertinents",
        "Sample combined text:": "Exemple de texte combiné :",
        "# Build TF-IDF matrix": "# Construire la matrice TF-IDF",
        "TF-IDF Matrix shape:": "Taille de la matrice TF-IDF :",
        "Vocabulary size:": "Taille du vocabulaire :",
        "# Compute cosine similarity": "# Calculer la similarité cosinus",
        "Similarity matrix shape:": "Taille de la matrice de similarité :",
        
        "# Find matching courses": "# Trouver les cours correspondants",
        "❌ Course not found": "❌ Cours non trouvé",
        "# Use the first match": "# Utiliser la première correspondance",
        "Found course:": "Cours trouvé :",
        "# Get similarity scores": "# Obtenir les scores de similarité",
        "# Skip the first one (itself) and get top_n + buffer": "# Ignorer le premier (soi-même) et prendre top_n + marge",
        "# Extract similarity values as numpy array for proper calculation": "# Extraire les valeurs de similarité en tableau numpy pour le calcul",
        "# Calculate final score (70% similarity + 30% popularity)": "# Calculer le score final (70% similarité + 30% popularité)",
        "# Return top recommendations": "# Retourner les meilleures recommandations",
        "# Only include columns that exist": "# Inclure uniquement les colonnes existantes",
        
        "# Test the recommendation system": "# Tester le système de recommandation",
        "COURSE RECOMMENDATIONS": "RECOMMANDATIONS DE COURS",
        "📚 Recommendations for:": "📚 Recommandations pour :",
        "# Example 1: Machine Learning": "# Exemple 1 : Machine Learning",
        "# Example 2: Python": "# Exemple 2 : Python",
        "# Example 3: Data Science": "# Exemple 3 : Data Science"
    }
    
    for en, fr in replacements.items():
        text = text.replace(en, fr)
    return text

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    for cell in nb['cells']:
        new_source = []
        for line in cell['source']:
            new_source.append(translate_text(line))
        cell['source'] = new_source

    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        
    print("Notebook translated successfully!")
    
except Exception as e:
    print(f"Error: {e}")
