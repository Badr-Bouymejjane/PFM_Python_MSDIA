# 🏁 Step-by-Step Implementation Guide

How the project was built from scratch to a working platform.

---

### Phase 1: Data Gathering (Scraping)

1. **Target Identification**: Selecting Coursera and Udemy as sources.
2. **Scraper Scripting**: Writing the Python scripts in `/scrapers` using BeautifulSoup and Playwright.
3. **Execution**: Running `run_scrapers.py` to fetch ~1100 courses.

### Phase 2: Data Engineering

1. **CSV Consolidation**: Merging raw files into `data/final_courses.csv`.
2. **Cleaning**: Standardizing column names (`partner` -> `instructor`, etc.).
3. **Enrichment**: Auto-generating categories for courses that lacked them using keyword matching in titles.

### Phase 3: ML Model Training

1. **Vectorization**: Running the TF-IDF transformer on the cleaned data.
2. **Similarity Precalculation**: Building the $1137 \times 1137$ similarity matrix.
3. **Persistence**: Saving the trained model to `models/recommender.pkl` for fast loading.

### Phase 4: User System & Backend

1. **UserManager**: Creating `user_manager.py` to handle JSON-based auth and behavior logging.
2. **Flask Routing**: Setting up routes for `/login`, `/courses`, and `/course/<id>`.
3. **Logic Integration**: Connecting the `recommender` to the web routes to display similar courses in the detail view.

### Phase 5: UI/UX & Visualization

1. **Template Design**: Building responsive Jinja2 templates.
2. **Clustering Implementation**: Integrating K-Means into the dashboard.
3. **Dynamic Filtering**: Adding real-time filters for Levels, Platforms, and Categories.

### Phase 6: Sync & Maintenance

1. **Integrity Checks**: Added code to detect if the CSV data has changed and auto-retrain the model.
2. **Filtering Noise**: Implemented logic to ignore invalid searches (similarity < 15%).
