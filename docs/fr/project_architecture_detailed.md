# Analyse Détaillée de l'Architecture du Projet

Ce document fournit une décomposition complète de l'architecture logicielle pour le **Système de Recommandation de Cours**. Il détaille l'organisation du code, les interactions entre composants et les modèles d'implémentation spécifiques utilisés à travers l'application.

## 1. Structure du Répertoire du Projet

Le projet suit une structure d'application Python modulaire standard, séparant les préoccupations en répertoires distincts pour le scraping, le traitement, la modélisation et la diffusion des données.

```
PFM_Python_MSDIA/
├── app.py                 # Point d'Entrée de l'Application (Serveur Flask)
├── config.py              # Configuration Centralisée
├── database.py            # Couche d'Interface Base de Données
├── user_manager.py        # Authentification Utilisateur & Couche Logique
├── data/                  # Stockage de Données (Brut, Traité, BD)
├── models/                # Logique d'Apprentissage Automatique
│   ├── recommender.py     # Moteur de Recommandation
│   └── clustering.py      # Clustering K-Means & Visualisation
├── scrapers/              # Modules de Collecte de Données
├── utils/                 # Utilitaires de Traitement de Données
├── templates/             # Modèles HTML (Jinja2)
└── static/                # CSS, JS et Images
```

## 2. Gestion de la Configuration (`config.py`)

Le fichier `config.py` agit comme la source centrale de vérité pour l'application, assurant la cohérence entre les modules. Il gère :
*   **Paramètres de Scraping** : Définit les plateformes cibles (`coursera`, `udemy`) et les catégories (`data-science`, `python`, etc.) pour faciliter l'expansion facile du jeu de données.
*   **Chemins de Données** : Gère les chemins de fichiers pour les CSV bruts et propres, utilisant une logique conditionnelle pour gérer les potentiels conflits de fusion ou différences d'environnement (branches `HEAD` vs `main`).
*   **Hyperparamètres ML** : Centralise les paramètres TF-IDF (`TFIDF_MAX_FEATURES=5000`, `NGRAM_RANGE=(1,2)`) pour assurer que les étapes d'entraînement et d'inférence utilisent des paramètres de vectorisation identiques.
*   **Paramètres Web** : Configurations hôte/port Flask et clés de sécurité (`SECRET_KEY`).

## 3. Architecture d'Apprentissage Automatique (`models/`)

L'intelligence centrale du système est encapsulée dans le paquet `models`, qui sépare la logique de recommandation de l'analyse de clustering.

### 3.1 Moteur de Recommandation (`models/recommender.py`)
La classe `CourseRecommender` implémente un système de **Filtrage Basé sur le Contenu**.
*   **Vectorisation** : Utilise `TfidfVectorizer` pour convertir un champ `combined_text` (Titre + Catégorie + Niveau) en vecteurs numériques clairsemés.
*   **Calcul de Similarité** : Calcule une matrice de similarité cosinus ($N \times N$) où $N$ est le nombre de cours.
*   **Persistance** : Implémente `save_model()` et `load_model()` utilisant `pickle` pour sérialiser :
    1.  Le `tfidf_vectorizer` ajusté (pour transformer les nouvelles requêtes).
    2.  La `tfidf_matrix` (pour éviter de re-calculer les vecteurs).
    3.  La `similarity_matrix` (pour une récupération O(1) des cours similaires).
*   **Traitement de Requête** : La méthode `recommend_by_query` transforme la recherche textuelle d'un utilisateur en un vecteur et trouve les voisins les plus proches dans l'espace vectoriel des cours.

### 3.2 Moteur de Clustering (`models/clustering.py`)
La classe `CourseClustering` fournit des analyses de haut niveau et des fonctionnalités exploratoires.
*   **Ingénierie des Fonctionnalités** : Crée une fonctionnalité `weighted_text` où la **Catégorie** est répétée 3 fois pour lui donner une importance plus élevée que le Titre lors de la vectorisation.
*   **Algorithme** : Utilise le **Clustering K-Means** (défaut `n_clusters=14`) pour grouper les cours en sujets sémantiques.
*   **Réduction de Dimensionnalité** : Applique **PCA (Analyse en Composantes Principales)** pour réduire les vecteurs TF-IDF de haute dimension en coordonnées 2D (`x`, `y`) pour la visualisation.
*   **Parcours d'Apprentissage** : Génère des "curriculums" structurés en triant les cours au sein d'un cluster par Niveau de Difficulté (`Beginner` -> `Intermediate` -> `Advanced`) puis par Note.

## 4. Couche Application (`app.py` & `user_manager.py`)

### 4.1 Serveur Web Flask (`app.py`)
*   **Gestion des Routes** : Mappe les URLs aux fonctions Python.
*   **Logique Hybride** : La route `home()` implémente la logique de recommandation hybride :
    *   *Étape 1* : Récupérer le Feedback Implicite (Clics Utilisateur).
    *   *Étape 2* : Récupérer le Feedback Explicite (Historique de Recherche).
    *   *Étape 3* : Interroger le `CourseRecommender` pour des cours similaires aux intérêts de l'utilisateur.
    *   *Étape 4* : Appliquer des indices de "Logique Métier" (ex: "Parce que vous avez vu X", "Populaire en Python").
*   **Décorateurs** : Utilise un décorateur personnalisé `@login_required` pour protéger les routes.

### 4.2 Logique Utilisateur (`user_manager.py`)
Abstrait les opérations liées aux utilisateurs de la couche HTTP.
*   Gère les flux d'Inscription/Connexion.
*   Met à jour les Statistiques Utilisateur (suivi des vues, recherches).
*   Calcule les Préférences Utilisateur (agrégation des comptes de catégories/niveaux depuis la base de données).

## 5. Couche d'Accès aux Données (`database.py`)

Encapsule toute interaction SQL pour prévenir les attaques par injection et organiser les requêtes.
*   **Schéma** :
    *   `users` : Données d'authentification.
    *   `searches` : Journaux de recherche.
    *   `clicks` : Journaux d'interaction (ID Cours + Horodatage).
    *   `favorites` : Listes organisées par l'utilisateur.
*   **Requêtes de Profilage** : Contient des agrégations SQL complexes (ex: `GROUP BY category ORDER BY count DESC`) pour transformer les journaux de clics bruts en profils utilisateurs exploitables.
