# Rapport Complet du Projet : Système de Recommandation de Cours

## 1. Résumé Exécutif

Ce projet est un **Système de Recommandation de Cours** sophistiqué conçu pour agréger, traiter et diffuser du contenu éducatif provenant des principales plateformes d'e-learning (Coursera et Udemy). Le système vise à fournir aux utilisateurs des recommandations de cours personnalisées, des analyses détaillées et une interface unifiée pour explorer les opportunités d'apprentissage à travers différents fournisseurs.

Le cycle de vie du projet comprend quatre phases principales :
1.  **Collecte de Données** : Scraping avancé de contenu web dynamique.
2.  **Traitement des Données** : Nettoyage rigoureux, normalisation et ingénierie des fonctionnalités (feature engineering).
3.  **Stockage & Gestion** : Implémentation d'une base de données relationnelle pour le suivi des utilisateurs et des interactions.
4.  **Application** : Une application web basée sur Flask avec authentification, un moteur de recommandation basé sur le ML, et des visualisations interactives.

---

## 2. Architecture du Projet

Le projet est structuré comme une application Python modulaire :

*   **`app.py`** : Le point d'entrée principal, hébergeant le serveur web Flask et la logique de routage.
*   **`scrapers/`** : Contient des scripts spécialisés pour extraire les données de Coursera et Udemy.
*   **`utils/`** : Abrite les classes utilitaires pour le nettoyage des données (`DataCleaner`) et l'ingénierie des fonctionnalités (`FeatureEngineer`).
*   **`models/`** : Contient la logique d'apprentissage automatique pour les recommandations (`CourseRecommender`) et le clustering (`CourseClustering`).
*   **`database.py`** : Gère les interactions SQLite pour les données utilisateurs, les préférences et le suivi.
*   **`data/`** : Stocke les jeux de données bruts, traités et finaux, ainsi que la base de données SQLite.
*   **`templates/` & `static/`** : Actifs frontend pour l'interface web.

---

## 3. Phase 1 : Collecte de Données (Scraping)

La fondation du projet est l'extraction automatisée des données de cours en utilisant **Playwright**, un outil puissant pour contrôler les navigateurs sans interface graphique (headless), essentiel pour gérer les pages web modernes et dynamiques.

### 3.1 Scraper Coursera (`scrapers/coursera_scraper.py`)
*   **Cible** : `https://www.coursera.org`
*   **Stratégie** :
    *   **Chargement Dynamique** : Gère le défilement infini par des actions de défilement programmatiques (`window.scrollBy`) pour déclencher le chargement différé (lazy-loading) du contenu.
    *   **Sélection Robuste** : Utilise plusieurs sélecteurs CSS redondants pour trouver les cartes de cours, assurant une résilience contre les changements d'interface utilisateur.
    *   **Gestion du Consentement** : Détecte et ferme automatiquement les popups de consentement aux cookies pour éviter l'obstruction.
    *   **Points de Données** : Extrait le Titre, l'Instructeur, la Note, les Avis, le Niveau, le Prix et les Compétences.

### 3.2 Scraper Udemy (`scrapers/udemy_scraper.py`)
*   **Cible** : `https://www.udemy.com`
*   **Stratégie** :
    *   **Pagination de Qualité Production** : Implémente une logique de pagination sophistiquée qui identifie et clique sur les boutons "Suivant" (gérant à la fois les balises `<a>` et `<button>`) pour parcourir plusieurs pages de résultats.
    *   **Extraction Basée sur les Cartes** : Cible des conteneurs de cartes de cours spécifiques (`section[class*="course-product-card"]`) et extrait les données en utilisant des attributs HTML sémantiques (ex: `data-purpose`).
    *   **Anti-Détection** : Utilise des techniques de furtivité (ex: désactivation des drapeaux `navigator.webdriver`) pour éviter d'être bloqué par les systèmes de détection de bots.
    *   **Points de Données** : Titre, URL, Instructeur, Note, Métadonnées (Durée, Conférences, Niveau), et Prix (Actuel vs Original).

---

## 4. Phase 2 : Traitement des Données & Feature Engineering

Une fois les données brutes collectées, elles subissent un pipeline strict pour assurer leur qualité et leur utilisabilité pour le moteur de recommandation.

### 4.1 Nettoyage des Données (`utils/data_cleaner.py`)
La classe `DataCleaner` transforme les scrapes bruts en un jeu de données structuré :
*   **Déduplication** : Supprime les entrées en double basées sur les titres des cours.
*   **Nettoyage de Texte** : Enlève les balises HTML, standardise les espaces, et gère les problèmes d'encodage (préservation des accents français).
*   **Normalisation** :
    *   **Catégories** : Mappe divers termes (ex: "AI", "Deep Learning") vers des catégories standardisées (ex: "Data Science", "Artificial Intelligence").
    *   **Niveaux** : Standardise les niveaux de difficulté (ex: "débutant" -> "Beginner").
    *   **Prix** : Catégorise les cours en "Free" (Gratuit), "Subscription" (Abonnement), ou "Paid" (Payant).
*   **Gestion des Données Manquantes** : Remplissage intelligent des valeurs par défaut pour les notes ou instructeurs manquants.

### 4.2 Ingénierie des Fonctionnalités (`utils/feature_engineering.py`)
La classe `FeatureEngineer` prépare les données pour l'Apprentissage Automatique :
*   **Préparation NLP** : Nettoie le texte en supprimant les mots vides (stopwords - supportant l'anglais et le français) et les caractères spéciaux. Crée un champ `combined_text` (Titre + Description + Compétences) pour la vectorisation TF-IDF.
*   **Encodages** : Convertit les variables catégorielles (Plateforme, Niveau, Prix) en formats numériques adaptés aux modèles.
*   **Normalisation** : Met à l'échelle les notes dans une plage de 0 à 1.
*   **Score de Popularité** : Calcule un score composite (`0.6 * rating_norm + 0.4 * reviews_norm`) pour classer les cours basés à la fois sur la qualité et la popularité.

---

## 5. Phase 3 : Stockage des Données & Gestion des Utilisateurs

### 5.1 Schéma de Base de Données (`database.py`)
L'application utilise **SQLite** (`data/recommandations.db`) pour le stockage persistant des données liées aux utilisateurs.
*   **`users`** : Stocke les détails d'authentification (mots de passe hachés).
*   **`searches`** : Enregistre les requêtes de recherche des utilisateurs pour affiner les futures recommandations.
*   **`clicks`** : Suit les interactions des utilisateurs (clics sur les cours) pour construire des profils de préférences implicites.
*   **`favorites`** : Permet aux utilisateurs de mettre des cours en favoris.

### 5.2 Profilage Utilisateur
*   **Préférences Implicites** : Le système calcule les préférences des utilisateurs dynamiquement en agrégeant leur historique de clics à travers les Catégories, Niveaux et Plateformes.
*   **Stats** : Suit les métriques d'engagement utilisateur (total des recherches, clics, favoris).

---

## 6. Phase 4 : Application & Utilisation

Le projet culmine dans une **Application Web Flask** riche en fonctionnalités (`app.py`).

### 6.1 Fonctionnalités Principales
*   **Authentification** : Système sécurisé d'Inscription et de Connexion.
*   **Tableau de Bord** : Une page d'accueil personnalisée montrant :
    *   **Recommandations de Recherches Récentes** : Suggestions basées sur les dernières requêtes de l'utilisateur.
    *   **Recommandations par Catégorie** : Sections "Parce que vous aimez [Catégorie]" dérivées de l'historique des clics.
    *   **Cours Populaires** : Recommandations de repli pour les nouveaux utilisateurs.
*   **Catalogue de Cours** : Une vue paginée, filtrable et triable de tous les cours.
*   **Recherche Intelligente** : Une barre de recherche pilotée par API qui fournit un retour visuel instantané.

### 6.2 Analytique Avancée
*   **Visualisation de Clustering** : La route `/clustering` visualise probablement le paysage sémantique des cours (utilisant des techniques comme t-SNE ou PCA sur des vecteurs TF-IDF), permettant aux utilisateurs d'"explorer" l'espace des cours visuellement.
*   **Parcours d'Apprentissage** : Le système peut suggérer une séquence de cours (`/api/learning-path`), guidant un utilisateur des sujets débutants aux sujets avancés au sein d'une catégorie.

### 6.3 Logique de Recommandation
*   **Filtrage Basé sur le Contenu** : Utilise TF-IDF sur les descriptions de cours pour trouver des "Cours Similaires".
*   **Score Hybride** : Le score final de recommandation est un mélange pondéré de :
    *   Similarité Textuelle (Correspondance sémantique).
    *   Correspondance des Préférences Utilisateur (Alignement Catégorie/Niveau).
    *   Popularité Globale (Note/Avis).
    *   Aléatoire "Optimiste" (Petites variations pour garder les résultats frais).

---

## 7. Conclusion

Ce projet représente un pipeline complet d'ingénierie de données et de science des données de bout en bout. Il relève avec succès les défis du scraping de plateformes web modernes, traite des données bruitées en un format propre et structuré, et exploite ces données pour alimenter une application web centrée sur l'utilisateur. L'inclusion du suivi des utilisateurs et de la personnalisation en fait non pas juste un annuaire, mais un moteur de découverte intelligent pour l'éducation en ligne.
