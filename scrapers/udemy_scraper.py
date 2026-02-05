"""
Udemy Scraper - Scrape courses from Udemy
Uses requests + BeautifulSoup for static content
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
import json

try:
    from config import CATEGORIES, MAX_COURSES_PER_CATEGORY, REQUEST_DELAY
except ImportError:
    CATEGORIES = ['data-science', 'machine-learning', 'python']
    MAX_COURSES_PER_CATEGORY = 30
    REQUEST_DELAY = 2


class UdemyScraper:
    """Scraper pour Udemy utilisant requests + BeautifulSoup"""
    
    BASE_URL = "https://www.udemy.com"
    SEARCH_URL = "https://www.udemy.com/courses/search/?q={query}&p={page}"
    API_URL = "https://www.udemy.com/api-2.0/courses/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.courses = []
        
    def search_courses(self, query, page=1):
        """Recherche des cours sur Udemy"""
        url = self.SEARCH_URL.format(query=query.replace(' ', '+'), page=page)
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"   ⚠️ Erreur requête: {e}")
            return None
            
    def parse_search_results(self, html, category):
        """Parse les résultats de recherche"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'lxml')
        courses = []
        
        # Chercher les cartes de cours
        course_cards = soup.select('div[data-component-class="course-card"]') or \
                       soup.select('.course-card') or \
                       soup.select('[class*="course-card"]')
                       
        # Alternative: chercher dans le JSON embarqué
        if len(course_cards) == 0:
            courses = self.extract_from_json(soup, category)
            return courses
            
        for card in course_cards:
            try:
                course = self.extract_course_from_card(card, category)
                if course and course.get('title'):
                    courses.append(course)
            except Exception as e:
                continue
                
        return courses
        
    def extract_from_json(self, soup, category):
        """Extrait les cours depuis les données JSON embarquées"""
        courses = []
        
        # Chercher les scripts avec des données JSON
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Course':
                            course = self.parse_json_course(item, category)
                            courses.append(course)
            except:
                pass
                
        # Chercher dans d'autres scripts
        all_scripts = soup.find_all('script')
        for script in all_scripts:
            if script.string and 'courseData' in str(script.string):
                try:
                    # Essayer d'extraire les données JSON
                    match = re.search(r'courseData["\s:]+(\[.*?\])', script.string, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        for item in data:
                            course = self.parse_json_course(item, category)
                            courses.append(course)
                except:
                    pass
                    
        return courses
        
    def parse_json_course(self, data, category):
        """Parse un cours depuis les données JSON"""
        return {
            'platform': 'Udemy',
            'title': data.get('name', data.get('title', '')),
            'description': data.get('description', '')[:500] if data.get('description') else '',
            'category': category.replace('-', ' ').title(),
            'skills': category.replace('-', ', '),
            'instructor': data.get('creator', {}).get('name', '') if isinstance(data.get('creator'), dict) else str(data.get('creator', '')),
            'rating': data.get('aggregateRating', {}).get('ratingValue', 0) if isinstance(data.get('aggregateRating'), dict) else 0,
            'num_reviews': data.get('aggregateRating', {}).get('reviewCount', 0) if isinstance(data.get('aggregateRating'), dict) else 0,
            'price': data.get('offers', {}).get('price', 'Paid') if isinstance(data.get('offers'), dict) else 'Paid',
            'level': 'Beginner',
            'language': 'English',
            'url': data.get('url', ''),
            'image_url': data.get('image', ''),
            'scraped_at': datetime.now().isoformat()
        }
        
    def extract_course_from_card(self, card, category):
        """Extrait les données d'une carte de cours"""
        course = {
            'platform': 'Udemy',
            'category': category.replace('-', ' ').title(),
            'scraped_at': datetime.now().isoformat()
        }
        
        # Titre
        title_elem = card.select_one('h3, h2, .course-title, [data-purpose="course-title"]')
        if title_elem:
            course['title'] = title_elem.get_text(strip=True)
            
        # Description
        desc_elem = card.select_one('.course-headline, [data-purpose="safely-set-inner-html"]')
        if desc_elem:
            course['description'] = desc_elem.get_text(strip=True)[:500]
        else:
            course['description'] = course.get('title', '')
            
        # Instructeur
        instructor_elem = card.select_one('.instructor-name, [data-purpose="instructor-name"]')
        if instructor_elem:
            course['instructor'] = instructor_elem.get_text(strip=True)
            
        # Rating
        rating_elem = card.select_one('[data-purpose="rating-number"], .star-rating-numeric')
        if rating_elem:
            try:
                course['rating'] = float(rating_elem.get_text(strip=True))
            except:
                pass
                
        # Nombre de reviews
        reviews_elem = card.select_one('[data-purpose="rating-count"], .reviews-count')
        if reviews_elem:
            try:
                text = reviews_elem.get_text(strip=True)
                num_match = re.search(r'([\d,]+)', text.replace(' ', ''))
                if num_match:
                    course['num_reviews'] = int(num_match.group(1).replace(',', ''))
            except:
                pass
                
        # Prix
        price_elem = card.select_one('.price-text--price-part, [data-purpose="course-price-text"]')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            if 'free' in price_text.lower():
                course['price'] = 'Free'
            else:
                course['price'] = price_text
                
        # Niveau
        level_elem = card.select_one('[data-purpose="course-level"], .course-level')
        if level_elem:
            course['level'] = level_elem.get_text(strip=True)
        else:
            course['level'] = 'All Levels'
            
        # URL
        link_elem = card.select_one('a[href*="/course/"]')
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('/'):
                course['url'] = self.BASE_URL + href
            else:
                course['url'] = href
                
        # Image
        img_elem = card.select_one('img[src*="udemy"]')
        if img_elem:
            course['image_url'] = img_elem.get('src', '')
            
        course['skills'] = category.replace('-', ', ')
        course['language'] = 'English'
        
        return course
        
    def scrape_category(self, category, max_courses=30):
        """Scrape les cours d'une catégorie"""
        print(f"\n🔍 Scraping Udemy: {category}")
        
        all_courses = []
        page = 1
        
        while len(all_courses) < max_courses:
            html = self.search_courses(category.replace('-', ' '), page)
            if not html:
                break
                
            courses = self.parse_search_results(html, category)
            if not courses:
                break
                
            all_courses.extend(courses)
            page += 1
            time.sleep(REQUEST_DELAY)
            
            if page > 3:  # Limiter les pages
                break
                
        print(f"   📦 Extrait {len(all_courses[:max_courses])} cours pour {category}")
        return all_courses[:max_courses]
        
    def scrape_all(self, categories=None, max_per_category=30):
        """Scrape toutes les catégories"""
        if categories is None:
            categories = CATEGORIES
            
        print("\n" + "="*60)
        print("   UDEMY SCRAPER")
        print("="*60)
        
        all_courses = []
        for i, category in enumerate(categories):
            print(f"\n[{i+1}/{len(categories)}] Catégorie: {category}")
            courses = self.scrape_category(category, max_per_category)
            all_courses.extend(courses)
            time.sleep(REQUEST_DELAY)
            
        self.courses = all_courses
        print(f"\n✅ Total: {len(all_courses)} cours scrapés de Udemy")
        
        return all_courses
        
    def to_dataframe(self):
        """Convertit les cours en DataFrame"""
        return pd.DataFrame(self.courses)
        
    def save_to_csv(self, filepath):
        """Sauvegarde les cours dans un fichier CSV"""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"💾 Sauvegardé: {filepath}")


def generate_sample_udemy_data(categories, max_per_category=30):
    """
    Génère des données d'exemple pour Udemy
    (utilisé si le scraping ne fonctionne pas à cause de protections anti-bot)
    """
    import random
    
    courses = []
    course_templates = [
        ("Complete {cat} Bootcamp", "Learn {cat} from scratch to advanced level"),
        ("{cat} Masterclass", "Master {cat} with hands-on projects"),
        ("The Ultimate {cat} Course", "Comprehensive guide to {cat}"),
        ("{cat} for Beginners", "Start your journey in {cat}"),
        ("Advanced {cat} Techniques", "Take your {cat} skills to the next level"),
        ("Professional {cat}", "Become a {cat} professional"),
        ("{cat} A-Z", "Everything you need to know about {cat}"),
        ("Practical {cat}", "Real-world {cat} applications"),
    ]
    
    instructors = [
        "Jose Portilla", "Angela Yu", "Colt Steele", "Stephen Grider",
        "Maximilian Schwarzmüller", "Brad Traversy", "Andrew Ng",
        "Tim Buchalka", "Rob Percival", "Dr. Angela Yu"
    ]
    
    for category in categories:
        cat_name = category.replace('-', ' ').title()
        
        for i in range(min(max_per_category, len(course_templates))):
            template = course_templates[i % len(course_templates)]
            
            courses.append({
                'platform': 'Udemy',
                'title': template[0].format(cat=cat_name),
                'description': template[1].format(cat=cat_name),
                'category': cat_name,
                'skills': category.replace('-', ', '),
                'instructor': random.choice(instructors),
                'rating': round(random.uniform(4.0, 5.0), 1),
                'num_reviews': random.randint(1000, 50000),
                'price': random.choice(['$9.99', '$12.99', '$19.99', '$49.99', 'Free']),
                'level': random.choice(['Beginner', 'Intermediate', 'Advanced', 'All Levels']),
                'language': 'English',
                'url': f'https://www.udemy.com/course/{category}-course-{i+1}/',
                'image_url': '',
                'scraped_at': datetime.now().isoformat()
            })
            
    return courses


if __name__ == "__main__":
    scraper = UdemyScraper()
    
    # Test avec quelques catégories
    test_categories = ['python', 'web-development', 'data-science']
    
    # Essayer le scraping réel
    courses = scraper.scrape_all(test_categories, max_per_category=10)
    
    # Si pas de résultats, utiliser les données d'exemple
    if len(courses) < 10:
        print("\n⚠️ Scraping limité, génération de données d'exemple...")
        courses = generate_sample_udemy_data(test_categories, 15)
        scraper.courses = courses
        
    if courses:
        scraper.save_to_csv('data/udemy_courses.csv')
        print(f"\n📊 Exemple de cours:")
        df = scraper.to_dataframe()
        print(df.head())
