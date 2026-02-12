# Comprehensive Project Report: Course Recommendation System

## 1. Executive Summary

This project is a sophisticated **Course Recommendation System** designed to aggregate, process, and serve educational content from major e-learning platforms (Coursera and Udemy). The system aims to provide users with personalized course recommendations, detailed analytics, and a unified interface to explore learning opportunities across different providers.

The project lifecycle encompasses four main phases:
1.  **Data Collection**: Advanced scraping of dynamic web content.
2.  **Data Processing**: rigorous cleaning, normalization, and feature engineering.
3.  **Storage & Management**: Relational database implementation for user and interaction tracking.
4.  **Application**: A Flask-based web application with authentication, an ML-based recommendation engine, and interactive visualizations.

---

## 2. Project Architecture

The project is structured as a modular Python application:

*   **`app.py`**: The main entry point, hosting the Flask web server and routing logic.
*   **`scrapers/`**: Contains specialized scripts for extracting data from Coursera and Udemy.
*   **`utils/`**: Houses utility classes for data cleaning (`DataCleaner`) and feature engineering (`FeatureEngineer`).
*   **`models/`**: (Inferred) Contains the machine learning logic for recommendations (`CourseRecommender`) and clustering (`CourseClustering`).
*   **`database.py`**: Manages SQLite interactions for user data, preferences, and tracking.
*   **`data/`**: Stores raw, processed, and final datasets, as well as the SQLite database.
*   **`templates/` & `static/`**: Frontend assets for the web interface.

---

## 3. Phase 1: Data Collection (Scraping)

The foundation of the project is the automated extraction of course data using **Playwright**, a powerful tool for controlling headless browsers, essential for handling modern, dynamic web pages.

### 3.1 Coursera Scraper (`scrapers/coursera_scraper.py`)
*   **Target**: `https://www.coursera.org`
*   **Strategy**:
    *   **Dynamic Loading**: Handles infinite scrolling by programmatic scroll actions (`window.scrollBy`) to trigger lazy-loading of content.
    *   **Robust Selection**: Uses multiple redundant CSS selectors to find course cards, ensuring resilience against UI changes.
    *   **Consent Handling**: Automatically detects and dismisses cookie consent popups to prevent obstruction.
    *   **Data Points**: Extracts Title, Instructor, Rating, Reviews, Level, Price, and Skills.

### 3.2 Udemy Scraper (`scrapers/udemy_scraper.py`)
*   **Target**: `https://www.udemy.com`
*   **Strategy**:
    *   **Production-Grade Pagination**: Implements a sophisticated pagination logic that identifies and clicks "Next" buttons (handling both `<a>` and `<button>` tags) to traverse multiple result pages.
    *   **Card-Based Extraction**: Targets specific course card containers (`section[class*="course-product-card"]`) and extracts data using semantic HTML attributes (e.g., `data-purpose`).
    *   **Anti-Detection**: Uses stealth techniques (e.g., disabling `navigator.webdriver` flags) to avoid being blocked by bot detection systems.
    *   **Data Points**: Title, URL, Instructor, Rating, Metadata (Duration, Lectures, Level), and Price (Current vs Original).

---

## 4. Phase 2: Data Processing & Feature Engineering

Once raw data is collected, it undergoes a strict pipeline to ensure quality and usability for the recommendation engine.

### 4.1 Data Cleaning (`utils/data_cleaner.py`)
The `DataCleaner` class transforms raw scrapings into a structured dataset:
*   **Deduplication**: Removes duplicate entries based on course titles.
*   **Text Cleaning**: Strips HTML tags, standardizes whitespace, and handles encoding issues (preserving French accents).
*   **Normalization**:
    *   **Categories**: Maps diverse terms (e.g., "AI", "Deep Learning") to standardized categories (e.g., "Data Science", "Artificial Intelligence").
    *   **Levels**: Standardizes difficulty levels (e.g., "débutant" -> "Beginner").
    *   **Prices**: Categorizes courses into "Free", "Subscription", or "Paid".
*   **Handling Missing Data**: intelligent filling of default values for missing ratings or instructors.

### 4.2 Feature Engineering (`utils/feature_engineering.py`)
The `FeatureEngineer` class prepares the data for Machine Learning:
*   **NLP Preparation**: Cleans text by removing stopwords (supporting both English and French) and special characters. Creates a `combined_text` field (Title + Description + Skills) for TF-IDF vectorization.
*   **Encodings**: Converts categorical variables (Platform, Level, Price) into numerical formats suitable for models.
*   **Normalization**: Scales ratings to a 0-1 range.
*   **Popularity Score**: Calculates a composite score (`0.6 * rating_norm + 0.4 * reviews_norm`) to rank courses based on both quality and popularity.

---

## 5. Phase 3: Data Storage & User Management

### 5.1 Database Schema (`database.py`)
The application uses **SQLite** (`data/recommandations.db`) for persistent storage of user-related data.
*   **`users`**: Stores authentication details (hashed passwords).
*   **`searches`**: Logs user search queries to refine future recommendations.
*   **`clicks`**: Tracks user interactions (clicks on courses) to build implicit preference profiles.
*   **`favorites`**: Allows users to bookmark courses.

### 5.2 User Profiling
*   **Implicit Preferences**: The system calculates user preferences dynamically by aggregating their click history across Categories, Levels, and Platforms.
*   **Stats**: Tracks user engagement metrics (total searches, clicks, favorites).

---

## 6. Phase 4: Application & Usage

The project culminates in a feature-rich **Flask Web Application** (`app.py`).

### 6.1 Core Features
*   **Authentication**: Secure Registration and Login system.
*   **Dashboard**: A personalized home page showing:
    *   **Recent Search Recommendations**: Suggestions based on the user's last queries.
    *   **Category-Based Recommendations**: "Because you like [Category]" sections derived from click history.
    *   **Popular Courses**: Fallback recommendations for new users.
*   **Course Catalog**: A paginated, filterable, and sortable view of all courses.
*   **Smart Search**: An API-driven search bar that provides instant visual feedback.

### 6.2 Advanced Analytics
*   **Clustering Visualization**: The `/clustering` route likely visualizes the semantic landscape of courses (using techniques like t-SNE or PCA on TF-IDF vectors), allowing users to "explore" the course space visually.
*   **Learning Paths**: The system can suggest a sequence of courses (`/api/learning-path`), guiding a user from beginner to advanced topics within a category.

### 6.3 Recommendation Logic
*   **Content-Based Filtering**: Uses TF-IDF on course descriptions to find "Similar Courses".
*   **Hybrid Scoring**: The final recommendation score is a weighted mix of:
    *   Text Similarity (Semantic match).
    *   User Preference Match (Category/Level alignment).
    *   Global Popularity (Rating/Reviews).
    *   "Optimistic" Randomness (Small variations to keep results fresh).

---

## 7. Conclusion

This project represents a complete end-to-end data engineering and data science pipeline. It successfully conquers the challenges of scraping modern web platforms, processes noisy data into a clean, structured format, and leverages this data to power a user-centric web application. The inclusion of user tracking and personalization makes it not just a directory, but a smart discovery engine for online education.
