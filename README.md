# 🎓 Course Explorer: ML-Powered Recommendation System

A state-of-the-art **Machine Learning** platform designed to help users discover, analyze, and master new skills. This system integrates real-time web scraping from **Coursera** and **Udemy**, advanced data processing, and a multi-model recommendation engine (Clustering + Content-Filtering).

---

## 🚀 Key Features

### 🔍 Search & Exploration

- **Hybrid Search**: Advanced search algorithm matching titles, categories, and partners.
- **Micro-Filters**: Precise filtering by platform, difficulty level (Beginner to Advanced), and duration.
- **Smart Catalog**: A responsive interface displaying 1000+ courses with detailed metadata.

### 🤖 Intelligent Engines (Machine Learning)

- **Engine 1: Content-Based Filtering**: Uses **TF-IDF Vectorization** and **Cosine Similarity** to suggest courses identical in content to your interests.
- **Engine 2: Behavioral Clustering**: Employs **K-Means Clustering** to group courses into thematic "clusters", allowing the discovery of related fields.
- **Engine 3: Learning Path Generator**: Automatically constructs a step-by-step roadmap from beginner to expert for any given skill.

### 📊 Interactive Dashboard

- **Real-Time Analytics**: Visualization of course distributions across categories.
- **Platform Insights**: Comparison of ratings and pricing between Coursera and Udemy.
- **Cluster Visualization**: Graphical representation of how courses are grouped by the ML model.

---

## 📁 Project Architecture

```
Recommandations/
├── app.py                 # Core Flask application & API routes
├── database.py            # SQLite management (Users, Searches, Tracking)
├── user_manager.py        # Authentication & Session logic
├── scrapers/              # Data Acquisition (Playwright & BeautifulSoup)
│   ├── coursera_scraper.py
│   ├── udemy_scraper.py
│   └── run_scrapers.py
├── data/                  # Data Storage
│   ├── final_courses_shuffled.csv # Main processed dataset
│   └── recommandations.db # Relational database
├── models/                # Machine Learning Core
│   ├── recommender.py     # Similarity-based engine
│   └── clustering.py      # K-Means grouping engine
├── templates/             # Modern UI (Jinja2)
│   ├── dashboard.html     # Visual analytics
│   ├── home.html          # User personalized portal
│   └── ...
└── static/                # Assets (Design System, JS, Icons)
```

---

## 🛠️ Installation & Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/Badr-Bouymejjane/PFM_Python_MSDIA.git
cd Recommandations

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Data Preparation (Optional)

If you wish to refresh the database with live data:

```bash
# Run scrapers
python scrapers/run_scrapers.py
```

### 3. Launch the Platform

```bash
python app.py
```

Visit: **[http://localhost:5000](http://localhost:5000)**

---

## 🧬 Machine Learning Deep Dive

### **Clustering Engine (K-Means)**

The system analyzes text features to create 14 distinct thematic clusters. This allows the system to understand that a user interested in "Python" might also benefit from "Data Engineering" or "Backend Development" even if the titles are different.

### **Recommendation Logic (TF-IDF)**

1. **Vectorization**: Transforms course descriptions into mathematical vectors.
2. **Similarity**: Calculates the angle between vectors (Cosine Similarity).
3. **Weighting**: Gives higher priority to courses with high ratings and popularity scores.

---

## � Technologies Used

- **Backend**: Flask (Python), SQLite
- **Machine Learning**: Scikit-Learn, NumPy, Pandas
- **Web Scraping**: Playwright, BeautifulSoup4
- **Frontend**: HTML5 (Semantic), Vanilla CSS (Modern Design System), Chart.js (Analytics)
- **Icons**: Lucide Icons

---

## 👨‍💻 Author

**SDIA Student - S7 Project**
_SDIA - S7 / Python / Project / Recommendations_

---

© 2024 Course Explorer Project. All rights reserved.
