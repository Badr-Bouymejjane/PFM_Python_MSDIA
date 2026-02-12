# Analyse Détaillée du Traitement des Données & de l'Ingénierie des Fonctionnalités

Ce document fournit une plongée technique approfondie dans la phase de **Traitement des Données**, où les données web brutes et non structurées sont transformées en un jeu de données numérique propre, optimisé pour les algorithmes d'Apprentissage Automatique. Ce processus est divisé en deux étapes distinctes : Nettoyage (assainissement) et Ingénierie (enrichissement).

## 1. Pipeline de Nettoyage des Données (`utils/data_cleaner.py`)

La classe `DataCleaner` repose sur une série d'opérations idempotentes pour standardiser les données provenant de sources hétérogènes (Coursera et Udemy).

### 1.1 Standardisation des Catégories
Les données scrapées contiennent souvent des noms de catégories fragmentés (ex: "AI", "Artificial Intelligence", "Neural Networks"). Le système utilise un dictionnaire de mapping robuste pour consolider ceux-ci en une taxonomie fixe :
*   **Entrée** : `['deep-learning', 'ml', 'neural networks']`
*   **Sortie** : `'Data Science'` ou `'Artificial Intelligence'` (selon la règle de mapping spécifique).
Cela garantit que le moteur de recommandation ne traite pas "Machine Learning" et "ML" comme deux sujets non liés.

### 1.2 Assainissement du Texte
*   **Suppression des Artefacts HTML** : Des motifs Regex (`<[^>]+>`) suppriment les balises HTML restantes qui auraient pu survivre à la phase de scraping.
*   **Fixes d'Encodage** : Gère spécifiquement les conflits Latin-1/UTF-8 pour assurer que les accents français (`é`, `à`, `ç`) sont affichés correctement.
*   **Normalisation des Espaces** : Remplace les espaces multiples ou sauts de ligne par un espace unique pour prévenir les problèmes de tokeniseur plus tard.

### 1.3 Stratégie de Déduplication
Les cours sont souvent listés sous plusieurs requêtes de recherche. Le nettoyeur supprime les doublons basés sur le champ **Titre**, en gardant la première occurrence.
```python
self.df.drop_duplicates(subset=['title'], keep='first')
```

## 2. Pipeline d'Ingénierie des Fonctionnalités (`utils/feature_engineering.py`)

La classe `FeatureEngineer` transforme le texte lisible par l'homme et les étiquettes catégorielles en vecteurs mathématiques.

### 2.1 Prétraitement NLP
Avant la vectorisation, les données textuelles subissent un prétraitement rigoureux :
1.  **Suppression des Mots Vides (Stopwords)** : Utilise un ensemble personnalisé de mots vides anglais et français (ex: "the", "le", "introduction", "course") pour supprimer les mots non informatifs.
2.  **Réduction de Bruit** : Supprime les URLs, les caractères spéciaux et les nombres isolés.
3.  **Combinaison** : Crée une fonctionnalité `combined_text` :
    $$ \text{Combiné} = \text{Titre} + \text{Description} + \text{Compétences} + \text{Catégorie} $$
    Ce champ agrégé est ce que le vectoriseur TF-IDF consomme réellement.

### 2.2 Encodage Numérique
Les modèles ML nécessitent une entrée numérique. Le système applique différentes stratégies d'encodage :
*   **Encodage Ordinal** : Utilisé pour le `Niveau` car il y a une hiérarchie claire :
    *   `All Levels` -> 0
    *   `Beginner` -> 1
    *   `Intermediate` -> 2
    *   `Advanced` -> 3
*   **Encodage Nominal** : Utilisé pour la `Plateforme` (`Coursera=1`, `Udemy=2`) et le `Prix` (`Free=0`, `Subscription=1`, `Paid=2`).

### 2.3 Le "Score de Popularité"
L'une des innovations clés de ce projet est le **Score de Popularité**, une métrique synthétique conçue pour classer les cours équitablement.
Les notes brutes sont souvent trompeuse (une note de 5.0 sur 1 avis est moins fiable qu'une de 4.8 sur 10 000 avis).

La formule utilisée est :
$$ \text{Popularité} = 0.6 \times \text{NoteNormalisée} + 0.4 \times \text{Log(AvisNormalisés)} $$

*   **Transformation Logarithmique** : Nous appliquons `np.log1p` au compte d'avis pour compresser l'échelle. Cela empêche les cours avec des millions d'avis de dominer complètement le score, permettant aux cours de haute qualité avec "seulement" quelques milliers d'avis de rivaliser.
*   **Moyenne Pondérée** : Nous donnons un peu plus de poids (60%) à la qualité (note) qu'à la quantité (avis).

### 2.4 Normalisation
Toutes les variables continues (Notes, Popularité) sont mises à l'échelle dans une plage `[0, 1]` pour assurer qu'elles contribuent également lors du calcul des distances ou des scores de similarité.
