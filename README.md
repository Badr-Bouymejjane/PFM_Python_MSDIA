# 🎓 CourseAI - Intelligent Course Recommender

CourseAI is a Python-based application that aggregates online courses from Coursera and Udemy, analyzes them, and provides personalized recommendations using a content-based filtering engine. It features a modern Streamlit dashboard for easy exploration.

## 🚀 Features

- **Multi-Platform Scraping**: Robust, stealthy scrapers for Coursera and Udemy using Playwright.
- **Data Standardization**: Unified data processing pipeline to clean and normalize course data (duration, ratings, difficulty).
- **Smart Recommendations**: TF-IDF & Cosine Similarity model to find the best courses matching your query.
- **Interactive Dashboard**: precise filtering, search, and analytics visualizations using Streamlit.

## 📂 Project Structure

```text
Full_PFM_Python/
├── app.py                      # Main Streamlit Dashboard
├── data/                       # Dataset storage (JSON & CSV)
├── docs/                       # Project Documentation & Architecture
├── lib/                        # Shared scraping logic & classes
├── scripts/                    # Utilities for scraping, cleaning, and training
│   ├── analyze_site.py         # DOM analysis tool
│   ├── clean_data.py           # Data cleaning pipeline
│   ├── consolidate_data.py     # Data merging utility
│   ├── scrape_courses.py       # Main scraping orchestrator
│   └── train_model.py          # Machine Learning recommendation engine
└── requirements.txt            # Project dependencies
```

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Badr-Bouymejjane/PFM_Python_MSDIA.git
    cd Full_PFM_Python
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

## 🏃 Usage

### 1. Run the Dashboard (Quick Start)
To use the existing dataset and explore courses:
```bash
streamlit run app.py
```

### 2. Collect New Data (Advanced)
To run the scrapers yourself:
```bash
# Run the mass scraper (configure limits in the script first)
python scripts/scrape_courses.py
```

### 3. Process Data
After scraping, clean and train the model:
```bash
# Consolidation (if multiple raw files exist)
python scripts/consolidate_data.py

# Cleaning
python scripts/clean_data.py
```

## 🤖 Tech Stack

- **Language**: Python 3.10+
- **Scraping**: Playwright, BeautifulSoup
- **Data**: Pandas, NumPy
- **ML**: Scikit-learn (TF-IDF)
- **UI**: Streamlit, Plotly

## 📝 License

This project is for educational purposes. Please respect the Terms of Service of the target websites when scraping.
