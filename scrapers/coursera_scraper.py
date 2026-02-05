"""
Coursera Scraper - Scrape courses from Coursera
Uses Playwright for dynamic content loading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import time

try:
    from config import CATEGORIES, MAX_COURSES_PER_CATEGORY, HEADLESS_MODE, REQUEST_DELAY
except ImportError:
    CATEGORIES = ['data-science', 'machine-learning', 'python']
    MAX_COURSES_PER_CATEGORY = 30
    HEADLESS_MODE = True
    REQUEST_DELAY = 2


class CourseraScraper:
    """Scraper pour Coursera utilisant Playwright"""
    
    BASE_URL = "https://www.coursera.org"
    SEARCH_URL = "https://www.coursera.org/search?query={query}"
    
    def __init__(self, headless=True):
        self.headless = headless
        self.courses = []
        
    async def init_browser(self):
        """Initialise le navigateur Playwright"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def close_browser(self):
        """Ferme le navigateur"""
        await self.browser.close()
        await self.playwright.stop()
        
    async def handle_cookie_consent(self):
        """Gère le popup de consentement cookies"""
        try:
            consent_selectors = [
                'button:has-text("Accept")',
                'button:has-text("Accepter")',
                'button[data-testid="accept-cookies"]',
                '#onetrust-accept-btn-handler'
            ]
            for selector in consent_selectors:
                try:
                    btn = self.page.locator(selector)
                    if await btn.count() > 0:
                        await btn.first.click()
                        await asyncio.sleep(1)
                        break
                except:
                    pass
        except:
            pass
            
    async def scroll_page(self, scroll_count=5):
        """Fait défiler la page pour charger plus de contenu"""
        for _ in range(scroll_count):
            await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(1)
            
    def extract_text(self, element, default=''):
        """Extrait le texte d'un élément de manière sécurisée"""
        try:
            return element.strip() if element else default
        except:
            return default
            
    async def scrape_category(self, category, max_courses=30):
        """Scrape les cours d'une catégorie"""
        print(f"\n🔍 Scraping Coursera: {category}")
        
        url = self.SEARCH_URL.format(query=category.replace('-', ' '))
        
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await self.handle_cookie_consent()
            await asyncio.sleep(3)
            await self.scroll_page(5)
            
            # Sélecteurs pour les cartes de cours
            card_selectors = [
                'li.cds-9.css-0.cds-11.cds-grid-item',
                'li.cds-9',
                'div[data-testid="search-result-card"]',
                'li[class*="ais-Hits-item"]'
            ]
            
            cards = []
            for selector in card_selectors:
                cards = await self.page.locator(selector).all()
                if len(cards) > 0:
                    print(f"   ✅ Trouvé {len(cards)} cours avec sélecteur: {selector[:30]}...")
                    break
                    
            if len(cards) == 0:
                print(f"   ⚠️ Aucun cours trouvé pour {category}")
                return []
                
            courses = []
            for i, card in enumerate(cards[:max_courses]):
                try:
                    course_data = await self.extract_course_data(card, category)
                    if course_data and course_data.get('title'):
                        courses.append(course_data)
                except Exception as e:
                    continue
                    
            print(f"   📦 Extrait {len(courses)} cours pour {category}")
            return courses
            
        except Exception as e:
            print(f"   ❌ Erreur scraping {category}: {e}")
            return []
            
    async def extract_course_data(self, card, category):
        """Extrait les données d'une carte de cours"""
        course = {
            'platform': 'Coursera',
            'category': category.replace('-', ' ').title(),
            'scraped_at': datetime.now().isoformat()
        }
        
        # Titre
        title_selectors = ['h3', 'h2', '[data-testid="product-card-title"]', '.product-name']
        for sel in title_selectors:
            try:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    course['title'] = await elem.first.inner_text()
                    break
            except:
                pass
                
        # Organisation/Instructeur
        org_selectors = ['p.cds-ProductCard-partnerNames', 'span[data-testid="partner-names"]', '.partner-name']
        for sel in org_selectors:
            try:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    course['instructor'] = await elem.first.inner_text()
                    break
            except:
                pass
                
        # Rating
        rating_selectors = ['[aria-label*="rating"]', 'span:has-text("stars")', '.ratings-text']
        for sel in rating_selectors:
            try:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    text = await elem.first.inner_text()
                    match = re.search(r'(\d+[.,]?\d*)', text)
                    if match:
                        course['rating'] = float(match.group(1).replace(',', '.'))
                    break
            except:
                pass
                
        # Nombre de reviews
        try:
            text = await card.inner_text()
            review_match = re.search(r'\(?([\d.,]+)\s*[KkMm]?\)?\s*(?:reviews?|avis|étudiants?|students?)', text, re.I)
            if review_match:
                num_str = review_match.group(1).replace(',', '.')
                num = float(num_str)
                if 'k' in text.lower():
                    num *= 1000
                elif 'm' in text.lower():
                    num *= 1000000
                course['num_reviews'] = int(num)
        except:
            pass
            
        # Niveau
        level_keywords = {
            'Beginner': ['débutant', 'beginner', 'introduct', 'basic'],
            'Intermediate': ['intermédiaire', 'intermediate', 'medium'],
            'Advanced': ['avancé', 'advanced', 'expert', 'professional']
        }
        
        try:
            text = await card.inner_text()
            text_lower = text.lower()
            for level, keywords in level_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    course['level'] = level
                    break
        except:
            pass
            
        # Prix
        try:
            text = await card.inner_text()
            if 'free' in text.lower() or 'gratuit' in text.lower():
                course['price'] = 'Free'
            else:
                price_match = re.search(r'[\$€£]\s*(\d+(?:[.,]\d{2})?)', text)
                if price_match:
                    course['price'] = price_match.group(0)
                else:
                    course['price'] = 'Subscription'
        except:
            pass
            
        # URL
        try:
            link = card.locator('a').first
            if await link.count() > 0:
                href = await link.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        course['url'] = self.BASE_URL + href
                    else:
                        course['url'] = href
        except:
            pass
            
        # Description (texte disponible)
        try:
            desc_selectors = ['p:not(.cds-ProductCard-partnerNames)', '.description']
            for sel in desc_selectors:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    course['description'] = await elem.first.inner_text()
                    break
        except:
            course['description'] = course.get('title', '')
            
        # Skills (extrait du texte)
        course['skills'] = category.replace('-', ', ')
        course['language'] = 'English'
        
        return course
        
    async def scrape_all(self, categories=None, max_per_category=30):
        """Scrape toutes les catégories"""
        if categories is None:
            categories = CATEGORIES
            
        print("\n" + "="*60)
        print("   COURSERA SCRAPER")
        print("="*60)
        
        await self.init_browser()
        
        all_courses = []
        for i, category in enumerate(categories):
            print(f"\n[{i+1}/{len(categories)}] Catégorie: {category}")
            courses = await self.scrape_category(category, max_per_category)
            all_courses.extend(courses)
            await asyncio.sleep(REQUEST_DELAY)
            
        await self.close_browser()
        
        self.courses = all_courses
        print(f"\n✅ Total: {len(all_courses)} cours scrapés de Coursera")
        
        return all_courses
        
    def to_dataframe(self):
        """Convertit les cours en DataFrame"""
        return pd.DataFrame(self.courses)
        
    def save_to_csv(self, filepath):
        """Sauvegarde les cours dans un fichier CSV"""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"💾 Sauvegardé: {filepath}")


async def main():
    """Fonction principale pour tester le scraper"""
    scraper = CourseraScraper(headless=HEADLESS_MODE)
    
    # Scraper quelques catégories pour le test
    test_categories = ['data-science', 'machine-learning', 'python']
    courses = await scraper.scrape_all(test_categories, max_per_category=20)
    
    if courses:
        scraper.save_to_csv('data/coursera_courses.csv')
        print(f"\n📊 Exemple de cours:")
        df = scraper.to_dataframe()
        print(df.head())
        
        
if __name__ == "__main__":
    asyncio.run(main())
