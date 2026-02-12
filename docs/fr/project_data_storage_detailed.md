# Analyse Détaillée du Stockage des Données & de la Gestion des Utilisateurs

Ce document détaille la phase de **Stockage des Données & Gestion des Utilisateurs**, se concentrant sur la couche de persistance (`database.py`) et l'enveloppe de logique métier (`user_manager.py`) qui alimente les fonctionnalités de personnalisation de l'application.

## 1. Architecture de Base de Données (SQLite)

L'application utilise **SQLite** pour sa fiabilité, sa configuration zéro, et sa capacité à gérer les niveaux de concurrence attendus pour ce projet. Le fichier de base de données est situé à `data/recommandations.db`.

### 1.1 Conception du Schéma
Le schéma est normalisé pour assurer l'intégrité des données tout en permettant des requêtes analytiques complexes.

#### Table `users`
*   **But** : Authentification et identité.
*   **Colonnes** :
    *   `id` (PK) : Entier auto-incrémental.
    *   `username` (Unique) : Pour la connexion.
    *   `email` (Unique) : Pour la communication (preuve future).
    *   `password` : Stocke les mots de passe **hachés SHA-256** (jamais en texte clair).
    *   `created_at`, `last_login` : Horodatages pour l'audit.

#### Table `clicks` (Feedback Implicite)
C'est la table la plus critique pour le moteur de recommandation. Elle enregistre l'intérêt passif de l'utilisateur.
*   **Colonnes** : `user_id`, `course_id`, `category`, `level`, `platform`, `timestamp`.
*   **Usage** : suivi granulaire de *ce qui* intéresse un utilisateur. Si un utilisateur clique sur cinq cours "Advanced Python", cette table capture cette intention même s'il ne les met pas en "favoris".

#### Table `searches` (Intention Explicite)
*   **But** : Capture ce que l'utilisateur *cherche*.
*   **Usage** : Utilisé pour faire apparaître des recommandations "Reprenez votre recherche" et comprendre la demande utilisateur.

#### Table `favorites` (Feedback Explicite)
*   **But** : Une liste organisée par l'utilisateur de cours sauvegardés pour une consultation ultérieure.

## 2. Gestion des Utilisateurs & Profilage

La classe `UserManager` agit comme une couche de service entre l'application Flask et les requêtes brutes de base de données.

### 2.1 Profilage Utilisateur Dynamique
L'une des fonctionnalités clés du système est qu'il ne repose **pas** sur des enquêtes utilisateurs statiques (ex: "Qu'est-ce qui vous intéresse ?"). Au lieu de cela, il construit un profil dynamiquement basé sur le comportement.

#### Calcul de Préférence (`database.get_user_preferences`)
Le système agrège la table `clicks` pour construire un histogramme des intérêts utilisateurs :
1.  **Intérêt de Catégorie** : `SELECT category, COUNT(*) FROM clicks ... GROUP BY category`
2.  **Intérêt de Niveau** : Détermine si l'utilisateur préfère le contenu "Beginner" ou "Advanced".
3.  **Loyauté de Plateforme** : Vérifie si l'utilisateur clique exclusivement sur des liens Coursera ou Udemy.

Ces données permettent au `CourseRecommender` de pondérer ses suggestions. Par exemple, si un utilisateur cherche "Web", le système priorisera "Advanced Web Dev on Udemy" si cela correspond à son profil historique.

### 2.2 Statistiques & Analytique
Le système fournit une vue "Profil" qui aide les utilisateurs à comprendre leurs propres habitudes d'apprentissage en interrogeant :
*   Total des cours consultés.
*   Top 3 des domaines favoris.
*   Historique de recherche récent.

## 3. Bonnes Pratiques de Sécurité

*   **Hachage de Mot de Passe** : Le système utilise `hashlib.sha256` pour saler et hacher les mots de passe avant le stockage.
*   **Paramétrage** : Toutes les requêtes SQL utilisent des placeholders `?` (ex: `WHERE username = ?`) pour prévenir les attaques par Injection SQL.
*   **Gestion des Ressources** : Les connexions à la base de données sont ouvertes et fermées par requête (utilisant le modèle de gestionnaire de contexte implicitement via des méthodes d'aide) pour prévenir les problèmes de verrouillage de fichier.
