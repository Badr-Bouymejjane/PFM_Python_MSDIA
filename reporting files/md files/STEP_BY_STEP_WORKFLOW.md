# 🏁 Guide d'Implémentation Étape par Étape

Comment le projet a été construit de zéro jusqu'à une plateforme fonctionnelle.

---

### Phase 1 : Collecte de Données (Scraping)

1. **Identification des Cibles** : Sélection de Coursera et Udemy comme sources.
2. **Scripting des Scrapers** : Écriture des scripts Python dans `/scrapers` utilisant BeautifulSoup et Playwright.
3. **Exécution** : Lancement des scripts d'exécution pour récupérer ~1100 cours.

### Phase 2 : Ingénierie des Données

1. **Consolidation CSV** : Fusion des fichiers bruts dans `data/final_courses.csv`.
2. **Nettoyage** : Standardisation des noms de colonnes (`partner` -> `instructor`, etc.).
3. **Enrichissement** : Génération automatique de catégories pour les cours qui en manquaient via correspondance de mots-clés dans les titres.

### Phase 3 : Entraînement des Modèles ML

1. **Vectorisation** : Exécution du transformateur TF-IDF sur les données nettoyées.
2. **Précalcul de Similarité** : Construction de la matrice de similarité $1137 \times 1137$.
3. **Persistance** : Sauvegarde du modèle entraîné dans `models/recommender.pkl` pour un chargement rapide.

### Phase 4 : Système Utilisateur & Backend

1. **Gestionnaire Utilisateur** : Création de `user_manager.py` pour gérer l'authentification basée sur JSON et la journalisation du comportement.
2. **Routage Flask** : Configuration des routes pour `/login`, `/courses` et `/course/<id>`.
3. **Intégration Logique** : Connexion du `recommender` aux routes web pour afficher des cours similaires dans la vue détaillée.

### Phase 5 : UI/UX & Visualisation

1. **Design des Templates** : Construction de templates Jinja2 réactifs.
2. **Implémentation Clustering** : Intégration de K-Means dans le tableau de bord.
3. **Filtrage Dynamique** : Ajout de filtres en temps réel pour les Niveaux, Plateformes et Catégories.

### Phase 6 : Synchro & Maintenance

1. **Vérifications d'Intégrité** : Ajout de code pour détecter si les données CSV ont changé et réentraîner automatiquement le modèle.
2. **Filtrage du Bruit** : Implémentation d'une logique pour ignorer les recherches invalides (similarité < 15%).
