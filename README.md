# 🎓 Explorateur de Cours : Système de Recommandation IA

Une plateforme **Machine Learning** de pointe conçue pour aider les utilisateurs à découvrir, analyser et maîtriser de nouvelles compétences. Ce système intègre le scraping web en temps réel de **Coursera** et **Udemy**, un traitement avancé des données et un moteur de recommandation multi-modèle (Clustering + Filtrage de Contenu).

---

## 🚀 Fonctionnalités Clés

### 🔍 Recherche & Exploration

- **Recherche Hybride** : Algorithme de recherche avancé correspondant aux titres, catégories et partenaires.
- **Micro-Filtres** : Filtrage précis par plateforme, niveau de difficulté (Débutant à Avancé) et durée.
- **Catalogue Intelligent** : Une interface responsive affichant plus de 1000 cours avec des métadonnées détaillées.

### 🤖 Moteurs Intelligents (Machine Learning)

- **Moteur 1 : Filtrage Basé sur le Contenu** : Utilise la **Vectorisation TF-IDF** et la **Similarité Cosinus** pour suggérer des cours au contenu identique à vos intérêts.
- **Moteur 2 : Clustering Comportemental** : Emploie le **Clustering K-Means** pour regrouper les cours en "clusters" thématiques, permettant la découverte de domaines connexes.
- **Moteur 3 : Générateur de Parcours d'Apprentissage** : Construit automatiquement une feuille de route étape par étape, de débutant à expert, pour n'importe quelle compétence donnée.

### 📊 Tableau de Bord Interactif

- **Analytique Temps Réel** : Visualisation de la distribution des cours par catégorie.
- **Insights Plateforme** : Comparaison des notes et des prix entre Coursera et Udemy.
- **Visualisation des Clusters** : Représentation graphique de la manière dont les cours sont regroupés par le modèle ML.

---

## 📁 Architecture du Projet

```
Recommandations/
├── app.py                 # Application Flask principale & routes API
├── database.py            # Gestion SQLite (Utilisateurs, Recherches, Suivi)
├── user_manager.py        # Logique d'Authentification & Session
├── scrapers/              # Acquisition de Données (Playwright & BeautifulSoup)
│   ├── coursera_scraper.py
│   ├── udemy_scraper.py
│   ├── run_coursera.py
│   └── run_udemy.py
├── data/                  # Stockage des Données
│   ├── final_courses_shuffled.csv # Dataset principal traité
│   └── recommandations.db # Base de données relationnelle
├── models/                # Cœur du Machine Learning
│   ├── recommender.py     # Moteur basé sur la similarité
│   ├── clustering.py      # Moteur de regroupement K-Means
├── templates/             # UI Moderne (Jinja2)
│   ├── dashboard.html     # Analytique visuelle
│   ├── home.html          # Portail personnalisé utilisateur
│   └── ...
└── static/                # Assets (Design System, JS, Icônes)
```

---

## 🛠️ Installation & Configuration

### 1. Configuration de l'Environnement

```bash
# Cloner le dépôt
git clone https://github.com/Badr-Bouymejjane/PFM_Python_MSDIA.git
cd Recommandations

# Installer les dépendances
pip install -r requirements.txt
playwright install chromium
```

### 2. Préparation des Données (Optionnel)

Si vous souhaitez rafraîchir la base de données avec des données en direct :

```bash
# Lancer les scrapers
python scrapers/run_coursera.py
python scrapers/run_udemy.py
```

### 3. Lancer la Plateforme

```bash
python app.py
```

Visitez : **[http://localhost:5000](http://localhost:5000)**

---

## 🧬 Plongée dans le Machine Learning

### **Moteur de Clustering (K-Means)**

Le système analyse les caractéristiques textuelles pour créer 14 clusters thématiques distincts. Cela permet au système de comprendre qu'un utilisateur intéressé par "Python" pourrait également bénéficier de "Data Engineering" ou "Backend Development" même si les titres sont différents.

### **Logique de Recommandation (TF-IDF)**

1. **Vectorisation** : Transforme les descriptions de cours en vecteurs mathématiques.
2. **Similarité** : Calcule l'angle entre les vecteurs (Similarité Cosinus).
3. **Pondération** : Donne une priorité plus élevée aux cours avec des notes élevées et des scores de popularité.

---

## 💻 Technologies Utilisées

- **Backend** : Flask (Python), SQLite
- **Machine Learning** : Scikit-Learn, NumPy, Pandas
- **Web Scraping** : Playwright, BeautifulSoup4
- **Frontend** : HTML5 (Sémantique), Vanilla CSS (Design System Moderne), Chart.js (Analytique)
- **Icônes** : Lucide Icons

---

## 👨‍💻 Auteur

**Étudiant SDIA - Projet S7**
_SDIA - S7 / Python / Projet / Recommandations_

---

© 2024 Projet Explorateur de Cours. Tous droits réservés.
