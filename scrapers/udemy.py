"""
UDEMY SCRAPER - PRODUCTION VERSION

This scraper:
1. Uses CARD-BASED extraction to capture all course data
2. Finds cards using: section[class*="course-product-card"]
3. Extracts data using direct selectors (h2 elements, data-purpose attributes)
4. Implements PAGINATION with Next link clicking (uses <a> tags, not buttons!)
5. Handles duplicate prevention with seen_urls tracking
6. Continues across multiple pages until target limit reached

Version: Production (Card-Based + Pagination)
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from playwright.async_api import async_playwright


# Configuration du répertoire de sortie pour les données brutes
RAW_DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR.mkdir(exist_ok=True)


class UdemyScraper:
    """Production Udemy scraper with card-based extraction and pagination."""
    
    def __init__(self, headless: bool = False):
        # Initialisation du scraper avec option pour le mode sans tête
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def start(self):
        """Start browser with stealth configuration."""
        # Démarrage de Playwright
        self.playwright = await async_playwright().start()
        
        # Lancement de Chromium avec une option pour masquer l'automatisation
        # '--disable-blink-features=AutomationControlled' aide à éviter la détection antibot
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Création d'un contexte isolé avec une configuration qui imite un utilisateur réel
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            # Viewport standard Full HD
            viewport={"width": 1920, "height": 1080}, 
            locale="en-US"
        )
        
        # Ouverture d'une nouvelle page
        self.page = await self.context.new_page()
        
        # Injection de script pour masquer la propriété 'webdriver' (technique furtive)
        await self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    async def stop(self):
        """Close browser."""
        # Fermeture propre de toutes les ressources
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def search_and_scrape(self, search_query: str, limit: int = 70) -> List[Dict[str, Any]]:
        """
        Search for courses and scrape with pagination using card-based extraction.
        
        Args:
            search_query: Topic to search for
            limit: Number of courses to scrape (default 70)
            
        Returns:
            List of course dictionaries
        """
        # Construction de l'URL de recherche Udemy
        search_url = f"https://www.udemy.com/courses/search/?q={search_query.replace(' ', '+')}"
        
        print(f"\n[STEP 1] Navigating to: {search_url}")
        # Navigation vers la page avec timeout de 60s
        await self.page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
        
        # Wait for JavaScript to render
        print(f"[STEP 2] Waiting for page to render...")
        # Pause explicite pour laisser le temps aux frameworks JS (React) de monter les composants
        await asyncio.sleep(8)
        
        # Scroll to load content
        print(f"[STEP 3] Scrolling to load content...")
        # Simulation de scroll humain pour charger les images et composants lazy-loaded
        for i in range(3):
            # Scroll de 800 pixels vers le bas
            await self.page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1.5)
        # Retour en haut de page
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        # Extract courses with pagination
        # Appel de la fonction principale d'extraction paginée
        print(f"[STEP 4] Extracting courses with pagination to reach {limit} courses...")
        courses = await self.extract_courses_with_pagination(limit)
        
        print(f"\n[OK] Scraped {len(courses)} courses")
        return courses
    
    async def extract_courses_with_pagination(self, limit: int) -> List[Dict[str, Any]]:
        """
        Extract courses using CORRECTED selectors with PAGINATION support.
        Clicks Next link to navigate through multiple pages until limit reached.
        """
        courses = []
        # Set pour éviter les doublons (basé sur l'URL)
        seen_urls = set()
        page_number = 1
        no_new_content_count = 0
        
        # Boucle principale : tant qu'on n'a pas atteint la limite demandée
        while len(courses) < limit:
            print(f"\n[PAGE {page_number}] Current: {len(courses)}/{limit} courses")
            
            # Liste des sélecteurs pour trouver les conteneurs de cartes de cours
            card_selectors = [
                'section[class*="course-product-card"]',
                'div.content-grid-item-module--item',
            ]
            
            cards = []
            # Recherche des cartes sur la page actuelle
            for selector in card_selectors:
                cards = await self.page.query_selector_all(selector)
                if cards:
                    print(f"[OK] Found {len(cards)} cards with: {selector}")
                    break
            
            if not cards:
                print(f"[ERROR] No course cards found on page {page_number}!")
                break
            
            # Process each card on current page
            # Extraction des données carte par carte
            new_courses_this_page = 0
            for i, card in enumerate(cards):
                if len(courses) >= limit:
                    break
                
                try:
                    # Extraction détaillée pour une carte
                    course_data = await self.extract_from_card(card)
                    
                    if not course_data:
                        continue
                    
                    url = course_data.get("url")
                    # Vérification anti-doublon
                    if not url or url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    courses.append(course_data)
                    new_courses_this_page += 1
                    
                    # Affichage bref pour le suivi
                    title = course_data.get('title', 'N/A')[:50]
                    rating = course_data.get('rating', 'N/A')
                    print(f"  [{len(courses)}] {title} (Rating: {rating})")
                
                except Exception as e:
                    print(f"  [ERROR] Card {i+1} failed: {e}")
                    continue
            
            # Vérification si on a trouvé de nouveaux cours sur cette page
            if new_courses_this_page == 0:
                no_new_content_count += 1
                print(f"[WARN] No new courses on page {page_number} (attempt {no_new_content_count}/3)")
                
                # Sécurité anti-boucle infinie si on reste bloqué sur la même page
                if no_new_content_count >= 3:
                    print(f"[STOP] No new content after 3 pages. Stopping.")
                    break
            else:
                no_new_content_count = 0
                print(f"[OK] Added {new_courses_this_page} new courses from page {page_number}")
            
            # Stop if we have enough
            if len(courses) >= limit:
                print(f"[SUCCESS] Reached target of {limit} courses!")
                break
            
            # Try to find and click Next link
            # Gestion de la pagination pour aller à la page suivante
            print(f"\n[ACTION] Looking for Next link...")
            
            # Scroll en bas pour s'assurer que le bouton 'Suivant' est chargé
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # IMPORTANT: Udemy utilise souvent des balises <a> et non des <button> pour la pagination
            # Liste de sélecteurs pour le bouton/lien Suivant
            next_element_selectors = [
                # Look for <a> elements in pagination
                'nav[aria-label*="Pagination"] a:not([aria-disabled="true"]):last-of-type',
                'nav[aria-label="Pagination"] a[class*="next"]',
                'nav[aria-label="Pagination"] a:last-child:not([aria-disabled])',
                # Fallback to buttons if needed
                'button[aria-label*="Next"]',
                'button[aria-label="Next page"]',
            ]
            
            next_element = None
            for selector in next_element_selectors:
                try:
                    next_element = await self.page.query_selector(selector)
                    if next_element:
                        # Vérification si l'élément est désactivé (fin de liste)
                        is_disabled = await next_element.get_attribute("aria-disabled")
                        if is_disabled != "true":  # Not disabled (check string "true")
                            print(f"[OK] Found Next link with: {selector}")
                            break
                        else:
                            next_element = None
                except Exception as e:
                    continue
            
            if not next_element:
                print(f"[STOP] No active Next link found. End of results.")
                break
            
            # Click Next element (works for both <a> and <button>)
            print(f"[CLICK] Clicking Next link...")
            try:
                await next_element.click()
                page_number += 1
                
                # Wait for new page to load
                print(f"[WAIT] Waiting for page {page_number} to load...")
                await asyncio.sleep(5)  # Wait for new content to load
                
                # Scroll to top of new page
                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] Failed to click Next link: {e}")
                break
        
        return courses[:limit]
    
    async def extract_from_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single card using DIRECT SELECTORS.
        
        Based on actual HTML structure:
        - Title: h2 (NOT h3!)
        - URL: a[href*="/course/"]
        - Instructor: span[data-purpose*="visible-instructors"]
        - Rating: span[data-purpose="rating-number"]
        - Other data: ul.tag-list-module--list > li
        - Price: div[data-purpose="course-price-text"]
        """
        try:
            data = {
                "platform": "Udemy",
                "scraped_at": datetime.now().isoformat()
            }
            
            # 1. TITLE - h2 (corrected from h3!)
            # Extraction du titre
            title_elem = await card.query_selector("h2 a div")
            if not title_elem:
                # Fallback: try just h2
                title_elem = await card.query_selector("h2")
            
            if title_elem:
                data["title"] = (await title_elem.inner_text()).strip()
            else:
                data["title"] = "N/A"
            
            # 2. URL - a[href*="/course/"]
            # Extraction du lien du cours
            url_elem = await card.query_selector('a[href*="/course/"]')
            if url_elem:
                url = await url_elem.get_attribute("href")
                if url:
                    if not url.startswith("http"):
                        url = f"https://www.udemy.com{url}"
                    data["url"] = url
                else:
                    return None
            else:
                return None
            
            # 3. INSTRUCTOR - span[data-purpose*="visible-instructors"]
            # Extraction du nom de l'instructeur
            instructor_elem = await card.query_selector('span[data-purpose*="visible-instructors"]')
            if instructor_elem:
                data["instructor"] = (await instructor_elem.inner_text()).strip()
            else:
                data["instructor"] = "N/A"
            
            # 4. RATING - span[data-purpose="rating-number"]
            # Extraction de la note
            rating_elem = await card.query_selector('span[data-purpose="rating-number"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                try:
                    data["rating"] = float(rating_text.strip())
                except:
                    data["rating"] = None
            else:
                data["rating"] = None
            
            # 5. EXTRACT FROM TAG LIST - ul.tag-list-module--list
            # Extraction des métadonnées (durée, nombre de lectures, niveau...)
            # This includes: reviews, duration, lectures, level
            tag_list = await card.query_selector('ul[class*="tag-list"]')
            if tag_list:
                tags_text = await tag_list.inner_text()
                
                # Parse tags
                import re
                
                # Reviews: "22,772 ratings"
                reviews_match = re.search(r'([\d,]+)\s*ratings?', tags_text)
                if reviews_match:
                    data["reviews"] = int(reviews_match.group(1).replace(',', ''))
                else:
                    data["reviews"] = None
                
                # Duration: "99 total hours"
                duration_match = re.search(r'([\d.]+)\s*total hours?', tags_text)
                if duration_match:
                    data["duration_hours"] = float(duration_match.group(1))
                else:
                    data["duration_hours"] = None
                
                # Lectures: "429 lectures"
                lectures_match = re.search(r'(\d+)\s*lectures?', tags_text)
                if lectures_match:
                    data["lectures"] = int(lectures_match.group(1))
                else:
                    data["lectures"] = None
                
                # Level: "All Levels", "Beginner", etc.
                level_keywords = ['All Levels', 'Beginner', 'Intermediate', 'Advanced', 'Expert']
                data["level"] = "N/A"
                for keyword in level_keywords:
                    if keyword in tags_text:
                        data["level"] = keyword
                        break
            else:
                data["reviews"] = None
                data["duration_hours"] = None
                data["lectures"] = None
                data["level"] = "N/A"
            
            # 6. PRICE - div[data-purpose="course-price-text"]
            # Extraction du prix actuel
            price_elem = await card.query_selector('div[data-purpose="course-price-text"]')
            if price_elem:
                price_text = await price_elem.inner_text()
                data["current_price"] = price_text.strip()
            else:
                data["current_price"] = "N/A"
            
            # 7. ORIGINAL PRICE - div[data-purpose="course-old-price-text"]
            # Extraction de l'ancien prix (avant promo)
            original_price_elem = await card.query_selector('div[data-purpose="course-old-price-text"]')
            if original_price_elem:
                original_price_text = await original_price_elem.inner_text()
                data["original_price"] = original_price_text.strip()
            else:
                data["original_price"] = "N/A"
            
            # Note: Students enrolled is NOT available on search cards
            data["students"] = None
            
            # Last updated
            data["last_updated"] = None
            
            return data
        
        except Exception as e:
            print(f"    [ERROR] Card extraction failed: {e}")
            return None


async def main():
    """Test the production scraper."""
    print("="*60)
    print("UDEMY SCRAPER V5 - PRODUCTION")
    print("="*60)
    print("\nFeatures:")
    print("  - Card-based extraction (h2 selectors, data-purpose attributes)")
    print("  - Multi-page pagination with Next link clicking")
    print("  - Duplicate prevention")
    print("="*60)
    
    scraper = UdemyScraper(headless=False)
    
    try:
        await scraper.start()
        print("\nBrowser started.")
        
        courses = await scraper.search_and_scrape("python", limit=5)
        
        if not courses:
            print("\n[FAILED] No courses scraped")
            print("[TIP] Check that you can see courses in the browser window")
            return
        
        # Save
        output_file = RAW_DATA_DIR / "udemy_v5_test.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(courses, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVED] {len(courses)} courses")
        print(f"[FILE] {output_file.absolute()}")
        
        # Display
        for i, course in enumerate(courses, 1):
            print(f"\n[Course {i}]")
            print(f"  Title:        {course['title'][:60]}")
            print(f"  Instructor:   {course['instructor']}")
            print(f"  Rating:       {course['rating']}")
            print(f"  Reviews:      {course['reviews']}")
            print(f"  Students:     {course['students']}")
            print(f"  Price:        {course['current_price']}")
            print(f"  Duration:     {course['duration_hours']} hours" if course['duration_hours'] else "  Duration:     N/A")
            print(f"  Lectures:     {course['lectures']}")
            print(f"  Level:        {course['level']}")
            print(f"  Last Updated: {course['last_updated']}")
            print(f"  URL:          {course['url'][:60]}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()
        print("\nBrowser closed.")


if __name__ == "__main__":
    asyncio.run(main())
