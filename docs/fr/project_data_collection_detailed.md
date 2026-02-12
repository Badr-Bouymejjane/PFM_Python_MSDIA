# Analyse Détaillée de la Collecte de Données (Note sur le Scraping)

Ce document détaille la phase de **Collecte de Données** du projet, qui implique des stratégies de scraping web sophistiquées pour récolter des données de cours depuis Coursera et Udemy. Le système exploite **Playwright (API Async)** pour gérer la nature dynamique et lourde en JavaScript de ces applications web modernes.

## 1. Technologie Centrale : Playwright & Asyncio

Contrairement au scraping traditionnel (ex: `requests` + `BeautifulSoup`), ce projet utilise une approche d'automatisation de navigateur headless.
*   **Exécution Asynchrone** : Construit sur `asyncio` de Python pour effectuer des opérations I/O non bloquantes, permettant une attente efficace des réponses réseau et des mises à jour DOM.
*   **Chromium Headless** : Simule un environnement utilisateur réel (rendu CSS/JS) sans la surcharge graphique, bien que `HEADLESS_MODE` puisse être basculé dans `config.py` pour le débogage.
*   **Isolation de Contexte** : Chaque session de scrape s'exécute dans un contexte de navigateur frais, assurant aucune fuite de cookie entre les exécutions.

## 2. Scraper Coursera (`scrapers/coursera_scraper.py`)

### 2.1 Cible & Défis
*   **Cible** : `https://www.coursera.org/search?query={category}`
*   **Défi** : Coursera utilise le "Défilement Infini" / Lazy Loading. Le contenu n'est pas présent dans la réponse HTML initiale mais est chargé via AJAX à mesure que l'utilisateur défile vers le bas.

### 2.2 Détails d'Implémentation
*   **Logique de Défilement** :
    Le scraper injecte du JavaScript pour faire défiler la fenêtre par programmation :
    ```python
    await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
    ```
    Il répète cette action plusieurs fois (`scroll_count=5`) avec des pauses pour permettre à l'application React de récupérer et rendre les nouvelles cartes de cours.

*   **Gestion du Consentement** :
    Une méthode robuste `handle_cookie_consent` tente de cliquer sur les boutons "Accept" ou "Accepter" pour dégager la vue. Elle cible plusieurs variations de sélecteurs connus (`button[data-testid="accept-cookies"]`, `#onetrust-accept-btn-handler`) pour être résiliente aux tests A/B de l'interface utilisateur.

*   **Sélecteurs Redondants** :
    Pour prévenir les ruptures lorsque Coursera met à jour ses noms de classes (qui sont souvent offusqués, ex: `css-0`), le scraper essaie une hiérarchie de sélecteurs :
    1.  `li.cds-9.css-0...` (Spécifique)
    2.  `div[data-testid="search-result-card"]` (Sémantique/Stable)
    3.  `li[class*="ais-Hits-item"]` (Repli)

## 3. Scraper Udemy (`scrapers/udemy_scraper.py`)

### 3.1 Cible & Défis
*   **Cible** : `https://www.udemy.com/courses/search/?q={topic}`
*   **Défi** : Udemy a une détection de bot stricte (vérifiant les drapeaux d'automatisation) et une pagination complexe qui varie (utilisant parfois des balises `<a>`, parfois des balises `<button>`).

### 3.2 Détails d'Implémentation
*   **Configuration Furtive** :
    Le scraper modifie l'empreinte du navigateur pour cacher sa nature automatisée :
    ```python
    args=["--disable-blink-features=AutomationControlled"]
    # ...
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    ```
    Cela empêche les scripts de détecter le drapeau `navigator.webdriver` couramment utilisé pour bloquer les bots.

*   **Pagination de Qualité Production** :
    Au lieu de deviner les URLs (`page=2`), le scraper interagit physiquement avec l'élément de pagination "Suivant".
    *   **Logique** : Il cherche l'élément "Suivant" en utilisant une liste de sélecteurs (gérant à la fois les éléments sémantiques `nav` et les boutons génériques).
    *   **Validation** : Vérifie les attributs `aria-disabled` pour déterminer si la dernière page a été atteinte.
    *   **Flux** : `Défiler vers le Bas` -> `Trouver Suivant` -> `Cliquer` -> `Attendre Inactivité Réseau`.

*   **Extraction Basée sur les Cartes** :
    Les données sont extraites en utilisant des requêtes structurelles strictes relatives à l'élément carte :
    *   **Titre** : `h2 a div` (Gère la structure imbriquée).
    *   **Métadonnées** : Analyse la `ul.tag-list` pour séparer "Avis", "Durée", et "Conférences" en utilisant des Regex.
    *   **Prix** : Distingue entre le prix actuel (`data-purpose="course-price-text"`) et le prix original (pour calculer les réductions implicites).

## 4. Gestion des Erreurs & Résilience
Les deux scrapers implémentent des modèles de programmation défensive :
*   **Blocs Try/Except** : Appliqués au niveau de chaque champ. Si l'extraction d'une "Note" échoue, le scraper le journalise et continue d'extraire le "Titre" plutôt que de faire planter la session entière.
*   **Timeouts** : Des attentes explicites (`timeout=30000`) et des intervalles de sommeil (`asyncio.sleep`) préviennent les conditions de course où le code s'exécute avant que le DOM ne soit prêt.
