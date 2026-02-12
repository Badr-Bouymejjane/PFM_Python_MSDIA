# 🧠 The ML Heart: How Recommendations Work

This report dives into the mathematical logic behind the course recommendations and clustering.

---

## 1. Feature Engineering (The Input)

To recommend courses, we translate human language into numbers.
We create a **Combined Text** field: `Title + Category + Level`.
Example: `[ "Machine Learning", "Data Science", "Beginner" ]` becomes `"machine learning data science beginner"`.

## 2. Text Representation: TF-IDF

We use **TF-IDF (Term Frequency-Inverse Document Frequency)**.

- **TF**: How often a word appears in a course.
- **IDF**: How unique that word is across the whole catalog.
  Words like "Python" or "React" get higher weights than common filler words like "the" or "how".

## 3. Measuring Distance: Cosine Similarity

Imagine every course is an arrow in a 900-dimensional space.

- To find "Similar Courses", we compute the **Cosine** of the angle between these arrows.
- An angle of **0° (Similarity = 1.0)** means the courses are virtually identical.
- An angle of **90° (Similarity = 0.0)** means they have nothing in common.

The formula used: `Similarity(A, B) = (A · B) / (||A|| × ||B||)`

## 4. Unsupervised Discovery: K-Means Clustering

The **K-Means** algorithm automatically finds patterns in our 1137 courses.

1. It chooses 10 central points (centroids).
2. It assigns every course to the nearest cluster.
3. It creates meaningful groups like "Business & Finance" or "Health & Fitness" without being told which is which.

## 5. Visualizing the Catalog: PCA

Our data has hundreds of features. Human eyes can only see 2 or 3.
**PCA (Principal Component Analysis)** is a mathematical projection that squashes hundreds of dimensions into just **X and Y coordinates**, preserving the most important variations.
This is what powers the interactive "Discovery Map" in the UI.

## 6. Real-time User Logic

The recommendations on the Home page are a **Weighted Hybrid**:

- **Search Intent (40%)**: Based on your last 3 keyword searches.
- **Preference Bias (40%)**: Based on the categories of course you clicked.
- **Popularity (20%)**: Based on course ratings to ensure quality.
- **Safety**: Queries that result in no similarity (less than 15%) are rejected to prevent model pollution.
