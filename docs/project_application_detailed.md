# Detailed Application & Usage Analysis

This document details the **Application Phase**, where the data and models converge into a user-facing product. The application is built with **Flask**, a lightweight Python web framework, and serves as the interface for the recommendation engine.

## 1. Core Web Architecture (`app.py`)

The application follows the **Model-View-Controller (MVC)** pattern (implicitly):
*   **Model**: Interactions with `CourseRecommender` (ML) and `UserManager` (DB).
*   **View**: Jinja2 templates (`templates/`) rendering dynamic HTML.
*   **Controller**: Flask route functions handling HTTP requests.

### 1.1 Authentication System
*   **Security**: Uses stricter session management (`SESSION_COOKIE_HTTPONLY`, `SAMESITE='Lax'`) to prevent XSS and CSRF attacks.
*   **Flow**:
    *   `/register`: Validates input length and password matching. Creates a DB entry with a hashed password.
    *   `/login`: Verifies credentials and sets a signed session cookie.
    *   `@login_required`: A custom decorator that intercepts unauthorized access to protected routes (like `/dashboard` or `/profile`) and redirects to login.

### 1.2 The Dashboard (`/home`)
The dashboard is the heart of the personalization engine. It aggregates three distinct data streams:
1.  **Recent Search Recs**: "Since you searched for 'Python'..."
    *   *Logic*: Retrieves the last 3 queries from the `searches` table and runs them through the recommender.
2.  **Category Affinity Recs**: "Because you like Data Science..."
    *   *Logic*: Analyzes user clicks. If 60% of clicks are on "Data Science", then 60% of these slots are filled with top-rated Data Science courses.
3.  **Cold Start Fallback**:
    *   *Logic*: If the user has no history, it displays universally popular courses based on the `popularity_score`.

## 2. Advanced Analytics & Visualization

### 2.1 Clustering Visualization (`/clustering`)
This module allows users to explore the "map" of the educational landscape.
*   **Technique**: Uses **K-Means Clustering** ($K=14$) on the TF-IDF vectors of all courses.
*   **Dimensionality Reduction**: Uses **PCA** (Principal Component Analysis) to compress the 5000-dimensional text vectors into 2D coordinates ($x, y$).
*   **Frontend**: These coordinates are sent to the frontend (likely rendered with a library like Chart.js or D3.js implicitly via the template) to visually plot courses. Users can see that "Web Development" courses cluster in one corner, while "Finance" courses cluster in another.

### 2.2 Dynamic Learning Paths (`/api/learning-path`)
The system generates structured curricula on the fly.
*   **Algorithm**:
    1.  Filter courses by a specific Category (e.g., "Machine Learning").
    2.  Sort them by Level (`Beginner` -> `Intermediate` -> `Advanced`).
    3.  Select the highest-rated course at each level.
*   **Result**: A step-by-step path: "Start with 'Intro to ML' (Beginner), then take 'Deep Learning Specialization' (Intermediate)..."

## 3. The Recommendation Logic

The system uses a **Hybrid Scoring Algorithm** to rank courses. It doesn't rely on a simple cosine similarity score.

### 3.1 The Formula
$$ \text{Final Score} = \text{Base Score} + \text{Bonuses} + \text{Randomness} $$

1.  **Base Score**: Derived from the source of the recommendation.
    *   *Search Match*: High base (e.g., 88%)
    *   *Category Match*: Medium base (e.g., 80%) + Boost based on user intensity.
    *   *Popularity*: Low base (e.g., 72%)

2.  **Bonuses**:
    *   **Rating Bonus**: $+ (Rating - 3.5) \times 4$. A 5-star course gets a bigger boost than a 4-star one.

3.  **Optimistic Randomness**:
    *   Adds small noise ($\pm 1.5\%$) to the score.
    *   *Purpose*: Prevents the dashboard from looking "stale". Even if the user's data hasn't changed, the order of recommendations shifts slightly on every refresh, encouraging exploration.

### 3.2 Smart Search API (`/api/search`)
*   **Real-time Feedback**: The frontend sends keystrokes to this API.
*   **Thresholding**: The system ignores search results if the top match has a low similarity score (<15%), preventing irrelevant results from cluttering the UI (e.g., searching for "asdf" won't return random courses).
