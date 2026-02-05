# 🎓 Course Recommendation System

A complete **Machine Learning-powered Course Recommendation Platform** that scrapes courses from Coursera and Udemy, builds a structured dataset, and provides personalized recommendations.

## 🚀 Features

- **Multi-Platform Scraping**: Scrapes courses from Coursera & Udemy
- **Large Dataset**: 1000+ courses with detailed metadata
- **ML Recommendation Engine**: TF-IDF + Cosine Similarity
- **Beautiful Web Interface**: Modern Flask web application
- **Personalized Recommendations**: Based on course similarity
- **Advanced Filtering**: By category, platform, level, price

## 📁 Project Structure

```
Recommandations/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── scrapers/
│   ├── __init__.py
│   ├── coursera_scraper.py    # Coursera scraping
│   ├── udemy_scraper.py       # Udemy scraping
│   └── run_scrapers.py        # Run all scrapers
├── data/
│   ├── courses_raw.csv        # Raw scraped data
│   └── courses_clean.csv      # Cleaned dataset
├── models/
│   ├── __init__.py
│   └── recommender.py         # ML Recommendation Engine
├── utils/
│   ├── __init__.py
│   ├── data_cleaner.py        # Data cleaning utilities
│   └── feature_engineering.py # Feature engineering
├── templates/
│   ├── base.html              # Base template
│   ├── home.html              # Home page
│   ├── courses.html           # All courses page
│   └── course_detail.html     # Course details + recommendations
└── static/
    ├── css/
    │   └── style.css          # Main stylesheet
    └── js/
        └── main.js            # Frontend JavaScript
```

## 🛠️ Installation

### 1. Clone the repository

```bash
cd Recommandations
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers (for Coursera)

```bash
playwright install chromium
```

## 🔄 Usage

### Step 1: Scrape Courses

```bash
python scrapers/run_scrapers.py
```

### Step 2: Clean Data

```bash
python utils/data_cleaner.py
```

### Step 3: Run Web Application

```bash
python app.py
```

Then open: **http://localhost:5000**

## 🌐 Web Routes

| Route             | Description                      |
| ----------------- | -------------------------------- |
| `/`               | Home page with search & filters  |
| `/courses`        | All courses with pagination      |
| `/course/<id>`    | Course details + recommendations |
| `/recommend/<id>` | API: Get recommended courses     |
| `/api/search`     | API: Search courses              |
| `/api/filter`     | API: Filter courses              |

## 🤖 ML Recommendation System

### Content-Based Filtering

1. **TF-IDF Vectorization** on `title + description + skills`
2. **Cosine Similarity** computation
3. **Top-N Recommendations** based on similarity score

### Example

> User clicks **"Machine Learning with Python"**
> → System recommends similar ML/AI courses

## 📊 Dataset Fields

| Field         | Description                        |
| ------------- | ---------------------------------- |
| `platform`    | Coursera / Udemy                   |
| `title`       | Course title                       |
| `description` | Course description                 |
| `category`    | AI, Web, Business, etc.            |
| `skills`      | Tags and skills                    |
| `instructor`  | Course instructor                  |
| `rating`      | Average rating (0-5)               |
| `num_reviews` | Number of reviews                  |
| `price`       | Course price                       |
| `level`       | Beginner / Intermediate / Advanced |
| `language`    | Course language                    |
| `url`         | Course URL                         |

## 🛠️ Technologies

- **Python 3.10+**
- **Flask** - Web framework
- **Pandas** - Data processing
- **Scikit-learn** - ML algorithms (TF-IDF, Cosine Similarity)
- **Playwright** - Web scraping (Coursera)
- **BeautifulSoup** - HTML parsing
- **HTML/CSS/JavaScript** - Frontend

## 👨‍💻 Author

- SDIA Student - S7 Python Project

## 📝 License

MIT License
