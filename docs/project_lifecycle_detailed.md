# Detailed Project Lifecycle & Architecture Analysis

This document provides an in-depth technical analysis of the four core phases of the **Course Recommendation System**, expanding on the executive summary to detail the specific engineering decisions, algorithms, and architectural patterns employed.

## Phase 1: Data Collection (Sophisticated Web Scraping)

The data collection phase is built to overcome the challenges of modern, single-page applications (SPAs) like Coursera and Udemy. Traditional HTTP requests (`requests`, `BeautifulSoup`) fail here because content is loaded dynamically via JavaScript.

### 1.1 Architecture: Headless Browser Automation
We utilize **Playwright** (Python asynchronous API) to control a headless Chromium browser. This allows the scraper to:
*   **Execute JavaScript**: Necessary for rendering React/Angular components used by target sites.
*   **Mimic User Behavior**: Scroll, click, and wait for network idle states, which is critical for triggering "lazy loading" of course cards.
*   **Context Isolation**: Each scraper instance runs in a fresh browser context, preventing cookie/cache contamination between runs.

### 1.2 Anti-Detection & Reliability Strategies
*   **Stealth Mode**: The Udemy scraper specifically disables the `navigator.webdriver` flag to evade bot detection scripts that check for automation tools.
*   **Dynamic Waiting**: Instead of hardcoded `sleep()`, the scrapers wait for specific DOM elements (e.g., course cards) to appear or for network activity to settle (`networkidle`), ensuring data is fully loaded before extraction.
*   **Consent Management**: A specialized handler (`handle_cookie_consent`) automatically detects and dismisses GDPR cookie banners that would otherwise obscure content or intercept clicks.

### 1.3 Pagination Logic
*   **Infinite Scroll (Coursera)**: The scraper programmatically scrolls (`window.scrollBy`) to the bottom of the page multiple times, triggering the AJAX requests that load subsequent batches of courses.
*   **Button Parsing (Udemy)**: The scraper implements complex logic to identify the "Next" page element. It handles semantic inconsistencies where the button might be an anchor tag (`<a>`) or a button (`<button>`) depending on the A/B test version of the site being served.

---

## Phase 2: Data Processing ( rigorous Cleaning & Feature Engineering)

Raw data scraped from the web is noisy, inconsistent, and unstructured. This phase transforms it into a clean, numerical dataset suitable for Machine Learning.

### 2.1 Cleaning Pipeline (`DataCleaner`)
The cleaning process is strict and sequential:
1.  **Deduplication**: Removing identical courses scraped from different search queries or pagination overlaps.
2.  **Text Sanitization**:
    *   **HTML Stripping**: Removing tags (`<br>`, `<div>`) and decoding entities (`&amp;`).
    *   **Unicode Normalization**: Preserving French accents while removing non-standard characters.
3.  **Categorical Normalization**:
    *   **Mapping**: Converting diverse scraped categories (e.g., "Deep Learning", "Neural Networks") into a standardized taxonomy (e.g., "Data Science") using a predefined keyword map.
    *   **Level Standardization**: Mapping terms like "Débutant", "Introductory" to a unified "Beginner" level.
4.  **Imputation**: Filling missing values with sensible defaults (e.g., `ratings=0.0` if missing, `instructor="Unknown"`).

### 2.2 Feature Engineering (`FeatureEngineer`)
This step prepares the data for the recommendation algorithms:
*   **TF-IDF Vectorization Prep**: Creating a `combined_text` field by concatenating `Title + Description + Skills`. This rich text field is later used to calculate cosine similarity between courses.
*   **Quantitative Features**:
    *   **Level Encoding**: Ordinal encoding (`Beginner=1`, `Intermediate=2`, `Advanced=3`, `All Levels=0`).
    *   **Platform Encoding**: Nominal encoding (`Coursera=1`, `Udemy=2`).
    *   **Price Encoding**: Categorizing into `Free=0`, `Subscription=1`, `Paid=2`.
*   **Computed Metrics**:
    *   **Popularity Score**: A custom engineered metric designed to balance rating quality with review quantity:
        $$ \text{Score} = 0.6 \times \text{NormalizedRating} + 0.4 \times \text{Log(Reviews)} $$
        This prevents a course with one 5-star review from ranking higher than a course with 4.8 stars and 10,000 reviews.

---

## Phase 3: Storage & Management (Relational Database)

The system moves beyond simple file storage to a relational model using **SQLite**, enabling complex queries about user behavior.

### 3.1 Database Schema Design
*   **User Identity**: The `users` table stores credential hashes (SHA-256) for security, never plain-text passwords.
*   **Interaction Tracking**:
    *   **`clicks` Table**: Records every course a user views. This is crucial for **implicit feedback**—knowing what a user *looks at* is often more valuable data than what they *say* they like.
    *   **`searches` Table**: Logs search queries to understand user intent and improve future search result relevance.
    *   **`favorites` Table**: Stores **explicit feedback**, representing strong user interest.

### 3.2 User Profiling Logic
The system dynamically builds a user profile by aggregating data from the `clicks` table. It calculates:
*   **Top Categories**: "The user has clicked on 'Data Science' courses 15 times and 'Web Dev' 2 times."
*   **Preferred Level**: "The user mostly clicks 'Advanced' courses."
This profile is recalculated in real-time to adjust recommendations instantly.

---

## Phase 4: Application (Flask & ML Integration)

The web application serves as the interface between the processed data, the database, and the user.

### 4.1 Hybrid Recommendation Engine
The recommender system (`CourseRecommender`) uses a hybrid approach:
1.  **Content-Based Filtering**:
    *   Uses **TF-IDF (Term Frequency-Inverse Document Frequency)** to convert course descriptions into mathematical vectors.
    *   Calculates **Cosine Similarity** to find courses that are semantically similar to a user's search query or their recently viewed courses.
2.  **Profile-Based Boosting**:
    *   Results are not just sorted by text similarity. The system applies a "boost" to courses that match the user's preferred categories (derived from DB profiles).
    *   *Example*: If a user searches "Python", courses in their favorite category "Data Science" get a score bump over "Web Development" Python courses.
3.  **Cold Start Handling**:
    *   For new users without history, the system falls back to the pre-calculated **Popularity Score** to show universally high-quality content.

### 4.2 Visualization & Analytics
*   **Cluster Analysis**: The `/clustering` route uses K-Means clustering on the TF-IDF vectors to group courses into 14 distinct semantic clusters. These are visualized to show the landscape of available topics (e.g., a "Web Dev" cluster, a "Math/Statistics" cluster).
*   **Dashboard**: A personalized view that visualizes the user's own learning journey (categories explored, platforms used) using Chart.js.
