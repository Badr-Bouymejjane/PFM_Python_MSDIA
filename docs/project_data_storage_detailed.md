# Detailed Data Storage & User Management Analysis

This document details the **Data Storage & User Management** phase, focusing on the persistence layer (`database.py`) and the business logic wrapper (`user_manager.py`) that powers the application's personalization features.

## 1. Database Architecture (SQLite)

The application uses **SQLite** for its reliability, zero-configuration setup, and ability to handle the concurrency levels expected for this project. The database file is located at `data/recommandations.db`.

### 1.1 Schema Design
The schema is normalized to ensure data integrity while enabling complex analytical queries.

#### `users` Table
*   **Purpose**: Authentication and identity.
*   **Columns**:
    *   `id` (PK): Auto-incrementing integer.
    *   `username` (Unique): For login.
    *   `email` (Unique): For communication (future proofing).
    *   `password`: Stores **SHA-256 hashed** passwords (never plain text).
    *   `created_at`, `last_login`: Timestamps for auditing.

#### `clicks` Table (Implicit Feedback)
This is the most critical table for the recommendation engine. It records passive user interest.
*   **Columns**: `user_id`, `course_id`, `category`, `level`, `platform`, `timestamp`.
*   **Usage**: granular tracking of *what* a user is interested in. If a user clicks five "Advanced Python" courses, this table captures that intent even if they don't "favorite" them.

#### `searches` Table (Explicit Intent)
*   **Purpose**: Captures what the user is *looking* for.
*   **Usage**: Used to surface "Resume your search" recommendations and understand user demand.

#### `favorites` Table (Explicit Feedback)
*   **Purpose**: A user-curated list of saved courses for later viewing.

## 2. User Management & Profiling

The `UserManager` class acts as a service layer between the Flask application and the raw database queries.

### 2.1 Dynamic User Profiling
One of the system's key features is that it does **not** rely on static user surveys (e.g., "What are you interested in?"). Instead, it builds a profile dynamically based on behavior.

#### Preference Calculation (`database.get_user_preferences`)
The system aggregates the `clicks` table to build a histogram of user interests:
1.  **Category Interest**: `SELECT category, COUNT(*) FROM clicks ... GROUP BY category`
2.  **Level Interest**: Determines if the user prefers "Beginner" or "Advanced" content.
3.  **Platform Loyalty**: Checks if the user exclusively clicks Coursera or Udemy links.

This data allows the `CourseRecommender` to weight its suggestions. For example, if a user searches for "Web", the system will prioritize "Advanced Web Dev on Udemy" if that matches their historical profile.

### 2.2 Statistics & Analytics
The system provides a "Profile" view that helps users understand their own learning habits by querying:
*   Total courses viewed.
*   Top 3 favorite domains.
*   Recent search history.

## 3. Security Best Practices

*   **Password Hashing**: The system uses `hashlib.sha256` to salt and hash passwords before storage.
*   **Parameterization**: All SQL queries use `?` placeholders (e.g., `WHERE username = ?`) to prevent SQL Injection attacks.
*   **Resource Management**: Database connections are opened and closed per-request (using the context manager pattern implicitly via helper methods) to prevent file lock issues.
