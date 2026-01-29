# 📘 CourseAI Developer Documentation

## 🏗️ Architecture

The project follows a modular pipeline architecture:

1.  **Data Collection Layer** (`lib/`, `scripts/scrape_courses.py`)
    - Uses `Playwright` to simulate real user interactions.
    - Captures dynamic content (JavaScript-rendered) from Coursera and Udemy.
    - Implements stealth techniques (User-Agents, delays) to avoid blocking.

2.  **Data Processing Layer** (`scripts/clean_data.py`)
    - **Normalization**: Converts "40 hours" and "3 Months" into standard integer hours.
    - **Encoding**: Maps "Beginner"/"Advanced" to numeric levels (1-3).
    - **Deduplication**: Removes overlapping courses based on URL hash.
    - **Output**: Produces `data/final_courses.csv` for the model.

3.  **Recommendation Engine** (`scripts/train_model.py`)
    - Loads the CSV data.
    - Computes TF-IDF vectors for course titles and descriptions.
    - Calculates Cosine Similarity matrix to find nearest neighbors.
    - Exported as a Python class `CourseRecommender` for easy import.

4.  **Presentation Layer** (`app.py`)
    - Built with `Streamlit`.
    - Features 3 main tabs: Dashboard (KPIs), Smart Search (Model Interface), and Dataset (Data Grid).

## 🗂️ File Details

- **`lib/scrape_coursera.py`**: Class-based scraper specific to Coursera's DOM structure. Handles pagination and infinite scrolling.
- **`lib/scrape_udemy.py`**: Class-based scraper for Udemy. Note: Udemy has high anti-bot protection; this scraper uses stealth headers.
- **`scripts/consolidate_data.py`**: Helper script to merge parallel scraping results (e.g., if you run multiple category scrapes in parallel terminals).

## 🔄 Workflow for Extension

To add a **New Data Source** (e.g., edX):

1.  Create `lib/scrape_edx.py` following the `CourseraScraper` pattern.
2.  Update `scripts/scrape_courses.py` to import and run the new scraper.
3.  Update `scripts/clean_data.py` to handle any specific field differences (e.g., how edX formats duration).
4.  Run the pipeline: Scrape -> Consolidate -> Clean -> Train.
