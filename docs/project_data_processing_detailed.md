# Detailed Data Processing & Feature Engineering Analysis

This document provides a technical deep-dive into the **Data Processing** phase, where raw, unstructured web data is transformed into a clean, numerical dataset optimized for Machine Learning algorithms. This process is split into two distinct stages: Cleaning (sanitization) and Engineering (enrichment).

## 1. Data Cleaning Pipeline (`utils/data_cleaner.py`)

The `DataCleaner` class relies on a series of idempotent operations to standardize data from heterogeneous sources (Coursera and Udemy).

### 1.1 Category Standardization
Scraped data often contains fragmented category names (e.g., "AI", "Artificial Intelligence", "Neural Networks"). The system utilizes a robust mapping dictionary to consolidate these into a fixed taxonomy:
*   **Input**: `['deep-learning', 'ml', 'neural networks']`
*   **Output**: `'Data Science'` or `'Artificial Intelligence'` (depending on the specific mapping rule).
This ensures that the recommendation engine doesn't treat "Machine Learning" and "ML" as two unrelated topics.

### 1.2 Text Sanitization
*   **HTML Artifact Removal**: Regex patterns (`<[^>]+>`) strip leftover HTML tags that might have survived the scraping phase.
*   **Encoding Fixes**: Specifically handles Latin-1/UTF-8 conflicts to ensure French accents (`é`, `à`, `ç`) are displayed correctly.
*   **Whitespace Normalization**: Replaces multiple spaces or newlines with a single space to prevent tokenizer issues later.

### 1.3 Deduplication Strategy
courses are often listed under multiple search queries. The cleaner removes duplicates based on the **Title** field, keeping the first occurrence.
```python
self.df.drop_duplicates(subset=['title'], keep='first')
```

## 2. Feature Engineering Pipeline (`utils/feature_engineering.py`)

The `FeatureEngineer` class transforms human-readable text and categorical labels into mathematical vectors.

### 2.1 NLP Preprocessing
Before vectorization, textual data undergoes rigorous preprocessing:
1.  **Stopword Removal**: Uses a custom set of English and French stopwords (e.g., "the", "le", "introduction", "course") to remove non-informative words.
2.  **Noise Reduction**: Removes URLs, special characters, and isolated numbers.
3.  **Combination**: Creates a `combined_text` feature:
    $$ \text{Combined} = \text{Title} + \text{Description} + \text{Skills} + \text{Category} $$
    This aggregate field is what the TF-IDF vectorizer actually consumes.

### 2.2 Numerical Encoding
ML models require numerical input. The system applies different encoding strategies:
*   **Ordinal Encoding**: Used for `Level` because there is a clear hierarchy:
    *   `All Levels` -> 0
    *   `Beginner` -> 1
    *   `Intermediate` -> 2
    *   `Advanced` -> 3
*   **Nominal Encoding**: Used for `Platform` (`Coursera=1`, `Udemy=2`) and `Price` (`Free=0`, `Subscription=1`, `Paid=2`).

### 2.3 The "Popularity Score"
One of the key innovations in this project is the **Popularity Score**, a synthetic metric designed to rank courses fairly.
Raw ratings are often misleading (a 5.0 rating from 1 review is less reliable than a 4.8 from 10,000).

The formula used is:
$$ \text{Popularity} = 0.6 \times \text{NormalizedRating} + 0.4 \times \text{Log(NormalizedReviews)} $$

*   **Log Transformation**: We apply `np.log1p` to the review count to compress the scale. This prevents courses with millions of reviews from completely dominating the score, allowing high-quality courses with "only" a few thousand reviews to compete.
*   **Weighted Average**: We give slightly more weight (60%) to the quality (rating) than to the quantity (reviews).

### 2.4 Normalization
All continuous variables (Ratings, Popularity) are scaled to a `[0, 1]` range to ensure they contribute equally when calculating distances or similarity scores.
