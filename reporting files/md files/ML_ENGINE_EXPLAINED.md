# 🧠 Le Cœur ML : Comment Fonctionnent les Recommandations

Ce rapport plonge dans la logique mathématique derrière les recommandations de cours et le clustering.

---

## 1. Feature Engineering (L'Entrée)

Pour recommander des cours, nous traduisons le langage humain en chiffres.
Nous créons un champ **Texte Combiné** : `Titre + Catégorie + Niveau`.
Exemple : `[ "Machine Learning", "Data Science", "Beginner" ]` devient `"machine learning data science beginner"`.

## 2. Représentation Textuelle : TF-IDF

Nous utilisons **TF-IDF (Term Frequency-Inverse Document Frequency)**.

- **TF (Fréquence du Terme)** : Combien de fois un mot apparaît dans un cours.
- **IDF (Fréquence Inverse de Document)** : À quel point ce mot est unique dans tout le catalogue.
  Des mots comme "Python" ou "React" obtiennent des poids plus élevés que des mots de remplissage courants comme "le" ou "comment".

## 3. Mesure de Distance : Similarité Cosinus

Imaginez chaque cours comme une flèche dans un espace à 900 dimensions.

- Pour trouver des "Cours Similaires", nous calculons le **Cosinus** de l'angle entre ces flèches.
- Un angle de **0° (Similarité = 1.0)** signifie que les cours sont virtuellement identiques.
- Un angle de **90° (Similarité = 0.0)** signifie qu'ils n'ont rien en commun.

La formule utilisée : `Similarité(A, B) = (A · B) / (||A|| × ||B||)`

## 4. Découverte Non Supervisée : Clustering K-Means

L'algorithme **K-Means** trouve automatiquement des motifs dans nos 1137 cours.

1. Il choisit 10 points centraux (centroïdes).
2. Il assigne chaque cours au cluster le plus proche.
3. Il crée des groupes significatifs comme "Business & Finance" ou "Santé & Fitness" sans qu'on lui dise lequel est lequel.

## 5. Visualisation du Catalogue : PCA

Nos données ont des centaines de caractéristiques. Les yeux humains ne peuvent en voir que 2 ou 3.
**PCA (Analyse en Composantes Principales)** est une projection mathématique qui écrase des centaines de dimensions en justes **coordonnées X et Y**, préservant les variations les plus importantes.
C'est ce qui alimente la "Carte de Découverte" interactive dans l'interface utilisateur.

## 6. Logique Utilisateur Temps Réel

Les recommandations sur la page d'Accueil sont un **Hybride Pondéré** :

- **Intention de Recherche (40%)** : Basé sur vos 3 dernières recherches par mots-clés.
- **Biais de Préférence (40%)** : Basé sur les catégories de cours sur lesquels vous avez cliqué.
- **Popularité (20%)** : Basé sur les notes des cours pour assurer la qualité.
- **Sécurité** : Les requêtes qui ne donnent aucune similarité (moins de 15%) sont rejetées pour éviter la pollution du modèle.
