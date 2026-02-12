# Analyse Détaillée de l'Application & de l'Utilisation

Ce document détaille la **Phase d'Application**, où les données et les modèles convergent en un produit orienté utilisateur. L'application est construite avec **Flask**, un framework web Python léger, et sert d'interface pour le moteur de recommandation.

## 1. Architecture Web Centrale (`app.py`)

L'application suit le motif **Modèle-Vue-Contrôleur (MVC)** (implicitement) :
*   **Modèle** : Interactions avec `CourseRecommender` (ML) et `UserManager` (BD).
*   **Vue** : Modèles Jinja2 (`templates/`) rendant du HTML dynamique.
*   **Contrôleur** : Fonctions de route Flask gérant les requêtes HTTP.

### 1.1 Système d'Authentification
*   **Sécurité** : Utilise une gestion de session plus stricte (`SESSION_COOKIE_HTTPONLY`, `SAMESITE='Lax'`) pour prévenir les attaques XSS et CSRF.
*   **Flux** :
    *   `/register` : Valide la longueur de l'entrée et la correspondance du mot de passe. Crée une entrée BD avec un mot de passe haché.
    *   `/login` : Vérifie les identifiants et définit un cookie de session signé.
    *   `@login_required` : Un décorateur personnalisé qui intercepte l'accès non autorisé aux routes protégées (comme `/dashboard` ou `/profil`) et redirige vers la connexion.

### 1.2 Le Tableau de Bord (`/home`)
Le tableau de bord est le cœur du moteur de personnalisation. Il agrège trois flux de données distincts :
1.  **Recs de Recherche Récente** : "Puisque vous avez cherché 'Python'..."
    *   *Logique* : Récupère les 3 dernières requêtes de la table `searches` et les passe dans le recommandeur.
2.  **Recs d'Affinité de Catégorie** : "Parce que vous aimez Data Science..."
    *   *Logique* : Analyse les clics utilisateurs. Si 60% des clics sont sur "Data Science", alors 60% de ces emplacements sont remplis avec les cours Data Science les mieux notés.
3.  **Repli Démarrage à Froid (Cold Start)** :
    *   *Logique* : Si l'utilisateur n'a pas d'historique, il affiche des cours universellement populaires basés sur le `popularity_score`.

## 2. Analytique Avancée & Visualisation

### 2.1 Visualisation de Clustering (`/clustering`)
Ce module permet aux utilisateurs d'explorer la "carte" du paysage éducatif.
*   **Technique** : Utilise le **Clustering K-Means** ($K=14$) sur les vecteurs TF-IDF de tous les cours.
*   **Réduction de Dimensionnalité** : Utilise **PCA** (Analyse en Composantes Principales) pour compresser les vecteurs texte de 5000 dimensions en coordonnées 2D ($x, y$).
*   **Frontend** : Ces coordonnées sont envoyées au frontend (probablement rendues avec une bibliothèque comme Chart.js ou D3.js implicitement via le modèle) pour tracer visuellement les cours. Les utilisateurs peuvent voir que les cours "Web Development" se regroupent dans un coin, tandis que les cours "Finance" se regroupent dans un autre.

### 2.2 Parcours d'Apprentissage Dynamiques (`/api/learning-path`)
Le système génère des curriculums structurés à la volée.
*   **Algorithme** :
    1.  Filtrer les cours par une Catégorie spécifique (ex: "Machine Learning").
    2.  Les trier par Niveau (`Beginner` -> `Intermediate` -> `Advanced`).
    3.  Sélectionner le cours le mieux noté à chaque niveau.
*   **Résultat** : Un chemin étape par étape : "Commencez par 'Intro to ML' (Beginner), puis prenez 'Deep Learning Specialization' (Intermediate)..."

## 3. La Logique de Recommandation

Le système utilise un **Algorithme de Score Hybride** pour classer les cours. Il ne repose pas sur un simple score de similarité cosinus.

### 3.1 La Formule
$$ \text{Score Final} = \text{Score de Base} + \text{Bonus} + \text{Aléatoire} $$

1.  **Score de Base** : Dérivé de la source de la recommandation.
    *   *Correspondance Recherche* : Base élevée (ex: 88%)
    *   *Correspondance Catégorie* : Base moyenne (ex: 80%) + Boost basé sur l'intensité utilisateur.
    *   *Popularité* : Base faible (ex: 72%)

2.  **Bonus** :
    *   **Bonus Note** : $+ (Note - 3.5) \times 4$. Un cours 5 étoiles obtient un plus gros boost qu'un cours 4 étoiles.

3.  **Aléatoire Optimiste** :
    *   Ajoute un petit bruit ($\pm 1.5\%$) au score.
    *   *But* : Empêche le tableau de bord de sembler "figé". Même si les données de l'utilisateur n'ont pas changé, l'ordre des recommandations change légèrement à chaque rafraîchissement, encourageant l'exploration.

### 3.2 API de Recherche Intelligente (`/api/search`)
*   **Retour Temps-Réel** : Le frontend envoie les frappes au clavier à cette API.
*   **Seuillage** : Le système ignore les résultats de recherche si la meilleure correspondance a un score de similarité faible (<15%), empêchant les résultats non pertinents d'encombrer l'IU (ex: chercher "asdf" ne retournera pas de cours aléatoires).
