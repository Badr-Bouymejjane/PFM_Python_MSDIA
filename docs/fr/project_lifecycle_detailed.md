# Analyse Détaillée du Cycle de Vie & de l'Architecture du Projet

Ce document fournit une analyse technique approfondie des quatre phases principales du **Système de Recommandation de Cours**, développant le résumé exécutif pour détailler les décisions d'ingénierie spécifiques, les algorithmes et les modèles architecturaux employés.

## Phase 1 : Collecte de Données (Scraping Web Sophistiqué)

La phase de collecte de données est conçue pour surmonter les défis des applications modernes à page unique (SPA) comme Coursera et Udemy. Les requêtes HTTP traditionnelles (`requests`, `BeautifulSoup`) échouent ici car le contenu est chargé dynamiquement via JavaScript.

### 1.1 Architecture : Automatisation de Navigateur Headless
Nous utilisons **Playwright** (API asynchrone Python) pour contrôler un navigateur Chromium headless (sans tête). Cela permet au scraper de :
*   **Exécuter le JavaScript** : Nécessaire pour le rendu des composants React/Angular utilisés par les sites cibles.
*   **Imiter le Comportement Utilisateur** : Défiler, cliquer et attendre les états d'inactivité réseau, ce qui est critique pour déclencher le "chargement différé" (lazy loading) des cartes de cours.
*   **Isolation de Contexte** : Chaque instance de scraper s'exécute dans un contexte de navigateur frais, empêchant la contamination des cookies/caches entre les exécutions.

### 1.2 Stratégies Anti-Détection & Fiabilité
*   **Mode Furtif** : Le scraper Udemy désactive spécifiquement le drapeau `navigator.webdriver` pour échapper aux scripts de détection de bots qui vérifient les outils d'automatisation.
*   **Attente Dynamique** : Au lieu de `sleep()` codés en dur, les scrapers attendent que des éléments DOM spécifiques (ex: cartes de cours) apparaissent ou que l'activité réseau se stabilise (`networkidle`), assurant que les données sont entièrement chargées avant l'extraction.
*   **Gestion du Consentement** : Un gestionnaire spécialisé (`handle_cookie_consent`) détecte et ferme automatiquement les bannières de cookies GDPR qui obscurciraient autrement le contenu ou intercepteraient les clics.

### 1.3 Logique de Pagination
*   **Défilement Infini (Coursera)** : Le scraper fait défiler la page par programmation (`window.scrollBy`) vers le bas plusieurs fois, déclenchant les requêtes AJAX qui chargent les lots suivants de cours.
*   **Analyse de Bouton (Udemy)** : Le scraper implémente une logique complexe pour identifier l'élément de page "Suivant". Il gère les incohérences sémantiques où le bouton pourrait être une balise ancre (`<a>`) ou un bouton (`<button>`) selon la version de test A/B du site servi.

---

## Phase 2 : Traitement des Données (Nettoyage Rigoureux & Ingénierie des Fonctionnalités)

Les données brutes extraites du web sont bruitées, incohérentes et non structurées. Cette phase les transforme en un jeu de données numérique propre adapté au Machine Learning.

### 2.1 Pipeline de Nettoyage (`DataCleaner`)
Le processus de nettoyage est strict et séquentiel :
1.  **Déduplication** : Suppression des cours identiques scrapés à partir de différentes requêtes de recherche ou chevauchements de pagination.
2.  **Assainissement du Texte** :
    *   **Suppression HTML** : Enlèvement des balises (`<br>`, `<div>`) et décodage des entités (`&amp;`).
    *   **Normalisation Unicode** : Préservation des accents français tout en supprimant les caractères non standards.
3.  **Normalisation Catégorielle** :
    *   **Mapping** : Conversion des diverses catégories scrapées (ex: "Deep Learning", "Neural Networks") en une taxonomie standardisée (ex: "Data Science") utilisant une carte de mots-clés prédéfinie.
    *   **Standardisation de Niveau** : Mapping de termes comme "Débutant", "Introductory" vers un niveau unifié "Beginner".
4.  **Imputation** : Remplissage des valeurs manquantes avec des défauts sensés (ex: `ratings=0.0` si manquant, `instructor="Unknown"`).

### 2.2 Ingénierie des Fonctionnalités (`FeatureEngineer`)
Cette étape prépare les données pour les algorithmes de recommandation :
*   **Prép. Vectorisation TF-IDF** : Création d'un champ `combined_text` en concaténant `Titre + Description + Compétences`. Ce champ de texte riche est utilisé plus tard pour calculer la similarité cosinus entre les cours.
*   **Fonctionnalités Quantitatives** :
    *   **Encodage de Niveau** : Encodage ordinal (`Beginner=1`, `Intermediate=2`, `Advanced=3`, `All Levels=0`).
    *   **Encodage de Plateforme** : Encodage nominal (`Coursera=1`, `Udemy=2`).
    *   **Encodage de Prix** : Catégorisation en `Free=0`, `Subscription=1`, `Paid=2`.
*   **Métriques Calculées** :
    *   **Score de Popularité** : Une métrique technique personnalisée conçue pour équilibrer la qualité de la note avec la quantité d'avis :
        $$ \text{Score} = 0.6 \times \text{RatingNormalisé} + 0.4 \times \text{Log(Avis)} $$
        Cela empêche un cours avec un seul avis 5 étoiles de se classer plus haut qu'un cours avec 4.8 étoiles et 10 000 avis.

---

## Phase 3 : Stockage & Gestion (Base de Données Relationnelle)

Le système va au-delà du simple stockage de fichiers vers un modèle relationnel utilisant **SQLite**, permettant des requêtes complexes sur le comportement utilisateur.

### 3.1 Conception du Schéma de Base de Données
*   **Identité Utilisateur** : La table `users` stocke les hachages d'identification (SHA-256) pour la sécurité, jamais les mots de passe en texte clair.
*   **Suivi des Interactions** :
    *   **Table `clicks`** : Enregistre chaque cours qu'un utilisateur consulte. C'est crucial pour le **feedback implicite** — savoir ce qu'un utilisateur *regarde* est souvent une donnée plus précieuse que ce qu'il *dit* aimer.
    *   **Table `searches`** : Enregistre les requêtes de recherche pour comprendre l'intention de l'utilisateur et améliorer la pertinence des résultats futurs.
    *   **Table `favorites`** : Stocke le **feedback explicite**, représentant un fort intérêt utilisateur.

### 3.2 Logique de Profilage Utilisateur
Le système construit dynamiquement un profil utilisateur en agrégeant les données de la table `clicks`. Il calcule :
*   **Top Catégories** : "L'utilisateur a cliqué sur des cours 'Data Science' 15 fois et 'Web Dev' 2 fois."
*   **Niveau Préféré** : "L'utilisateur clique principalement sur des cours 'Advanced'."
Ce profil est recalculé en temps réel pour ajuster les recommandations instantanément.

---

## Phase 4 : Application (Intégration Flask & ML)

L'application web sert d'interface entre les données traitées, la base de données et l'utilisateur.

### 4.1 Moteur de Recommandation Hybride
Le système de recommandation (`CourseRecommender`) utilise une approche hybride :
1.  **Filtrage Basé sur le Contenu** :
    *   Utilise **TF-IDF (Term Frequency-Inverse Document Frequency)** pour convertir les descriptions de cours en vecteurs mathématiques.
    *   Calcule la **Similarité Cosinus** pour trouver des cours qui sont sémantiquement similaires à la requête de recherche d'un utilisateur ou à ses cours récemment consultés.
2.  **Boosting Basé sur le Profil** :
    *   Les résultats ne sont pas seulement triés par similarité textuelle. Le système applique un "boost" aux cours qui correspondent aux catégories préférées de l'utilisateur (dérivées des profils DB).
    *   *Exemple* : Si un utilisateur cherche "Python", les cours dans sa catégorie favorite "Data Science" obtiennent une augmentation de score par rapport aux cours Python "Web Development".
3.  **Gestion du Démarrage à Froid (Cold Start)** :
    *   Pour les nouveaux utilisateurs sans historique, le système se rabat sur le **Score de Popularité** pré-calculé pour montrer du contenu universellement de haute qualité.

### 4.2 Visualisation & Analytique
*   **Analyse de Cluster** : La route `/clustering` utilise le clustering K-Means sur les vecteurs TF-IDF pour grouper les cours en 14 clusters sémantiques distincts. Ceux-ci sont visualisés pour montrer le paysage des sujets disponibles (ex: un cluster "Web Dev", un cluster "Math/Statistics").
*   **Tableau de Bord** : Une vue personnalisée qui visualise le propre parcours d'apprentissage de l'utilisateur (catégories explorées, plateformes utilisées) en utilisant Chart.js.
