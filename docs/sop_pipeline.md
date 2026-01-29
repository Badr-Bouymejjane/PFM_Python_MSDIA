# 🏗️ SOP: DATA PIPELINE

## 1. Data Cleaning (Raw -> Processed)
- **Input:** `.tmp/data/raw_*.json`
- **Output:** `.tmp/data/processed_courses.parquet`
- **Rules:**
    - `price`: If "Free", set 0.0. If missing, set NaN.
    - `rating`: Extract float from "4.8 (1.2k reviews)".
    - `duration`: Convert "1-3 Months" or "Approx. 20 hours" to estimated hours (float).
    - `level`: Map to Ordinal (Beginner=1, Intermediate=2, Advanced=3).

## 2. Feature Engineering (Processed -> ML)
- **Input:** `.tmp/data/processed_courses.parquet`
- **Output:** `.tmp/models/tfidf_matrix.pkl`
- **Logic:**
    - Combine `title` + `description` + `skills`.
    - `TfidfVectorizer(stop_words='english', max_features=5000)`.
    - Compute Cosine Similarity Matrix.

## 3. Recommendation Logic
- Function `recommend(course_name, top_n=5)`:
    - Find index of `course_name`.
    - Get similarity scores.
    - Sort failing descending.
    - Return Top N.
