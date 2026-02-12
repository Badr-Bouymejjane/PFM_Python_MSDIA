# Detailed Project Architecture Analysis

This document provides a comprehensive breakdown of the software architecture for the **Course Recommendation System**. It details the code organization, component interactions, and specific implementation patterns used throughout the application.

## 1. Project Directory Structure

The project follows a standard modular Python application structure, separating concerns into distinct directories for scraping, processing, modeling, and serving data.

```
PFM_Python_MSDIA/
├── app.py                 # Application Entry Point (Flask Server)
├── config.py              # Centralized Configuration
├── database.py            # Database Interface Layer
├── user_manager.py        # User Authentication & Logic Layer
├── data/                  # Data Storage (Raw, Processed, Database)
├── models/                # Machine Learning Logic
│   ├── recommender.py     # Recommendation Engine
│   └── clustering.py      # K-Means Clustering & Visualization
├── scrapers/              # Data Collection Modules
├── utils/                 # Data Processing Utilities
├── templates/             # HTML Templates (Jinja2)
└── static/                # CSS, JS, and Images
```

## 2. Configuration Management (`config.py`)

The `config.py` file acts as the central source of truth for the application, ensuring consistency across modules. It handles:
*   **Scraping Settings**: Defines target platforms (`coursera`, `udemy`) and categories (`data-science`, `python`, etc.) to facilitate easy expansion of the dataset.
*   **Data Paths**: Manages file paths for raw and clean CSVs, utilizing conditional logic to handle potential merge conflicts or environment differences (`HEAD` vs `main` branches).
*   **ML Hyperparameters**: Centralizes TF-IDF settings (`TFIDF_MAX_FEATURES=5000`, `NGRAM_RANGE=(1,2)`) to ensure the training and inference stages use identical vectorization parameters.
*   **Web Settings**: Flask host/port configurations and security keys (`SECRET_KEY`).

## 3. Machine Learning Architecture (`models/`)

The core intelligence of the system is encapsulated in the `models` package, which separates recommendation logic from clustering analysis.

### 3.1 Recommendation Engine (`models/recommender.py`)
The `CourseRecommender` class implements a **Content-Based Filtering** system.
*   **Vectorization**: Uses `TfidfVectorizer` to convert a `combined_text` field (Title + Category + Level) into sparse numerical vectors.
*   **Similarity Calculation**: Computes a cosine similarity matrix ($N \times N$) where $N$ is the number of courses.
*   **Persistence**: Implements `save_model()` and `load_model()` using `pickle` to serialize:
    1.  The fitted `tfidf_vectorizer` (to transform new queries).
    2.  The `tfidf_matrix` (to avoid re-computing vectors).
    3.  The `similarity_matrix` (for O(1) retrieval of similar courses).
*   **Query Processing**: The `recommend_by_query` method transforms a user's text search into a vector and finds the nearest neighbors in the course vector space.

### 3.2 Clustering Engine (`models/clustering.py`)
The `CourseClustering` class provides high-level analytics and exploratory features.
*   **Feature Engineering**: Creates a `weighted_text` feature where the **Category** is repeated 3 times to give it higher importance than the Title during vectorization.
*   **Algorithm**: Uses **K-Means Clustering** (default `n_clusters=14`) to group courses into semantic topics.
*   **Dimensionality Reduction**: Applies **PCA (Principal Component Analysis)** to reduce high-dimensional TF-IDF vectors into 2D coordinates (`x`, `y`) for visualization.
*   **Learning Paths**: Generates structured "curricula" by sorting courses within a cluster by Difficulty Level (`Beginner` -> `Intermediate` -> `Advanced`) and then by Rating.

## 4. Application Layer (`app.py` & `user_manager.py`)

### 4.1 Flask Web Server (`app.py`)
*   **Route Handling**: Maps URLs to Python functions.
*   **Hybrid Logic**: The `home()` route implements the hybrid recommendation logic:
    *   *Step 1*: Retrieve Implicit Feedback (User Clicks).
    *   *Step 2*: Retrieve Explicit Feedback (Search History).
    *   *Step 3*: Query the `CourseRecommender` for courses similar to the user's interests.
    *   *Step 4*: Apply "Business Logic" hints (e.g., "Because you viewed X", "Popular in Python").
*   **Decorators**: Uses a custom `@login_required` decorator to protect routes.

### 4.2 User Logic (`user_manager.py`)
Abstracts user-related operations from the HTTP layer.
*   Handles Registration/Login flows.
*   Updates User Statistics (tracking views, searching).
*   Calculates User Preferences (aggregating category/level counts from the database).

## 5. Data Access Layer (`database.py`)

Encapsulates all SQL interaction to prevent injection attacks and organize queries.
*   **Schema**:
    *   `users`: Authentication data.
    *   `searches`: Search logs.
    *   `clicks`: Interaction logs (Course ID + Timestamp).
    *   `favorites`: User-curated lists.
*   **Profiling Queries**: Contains complex SQL aggregations (e.g., `GROUP BY category ORDER BY count DESC`) to transform raw click logs into actionable user profiles.
