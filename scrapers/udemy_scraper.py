"""
SCRAPER UDEMY - VERSION DE PRODUCTION

Ce scraper (robot d'extraction) :
1. Utilise l'extraction basée sur les CARTES pour capturer toutes les données des cours
2. Trouve les cartes en utilisant : section[class*="course-product-card"]
3. Extrait les données avec des sélecteurs directs (éléments h2, attributs data-purpose)
4. Implémente la PAGINATION en cliquant sur le lien Suivant (utilise les balises <a> !)
5. Gère la prévention des doublons avec le suivi des URL vues
6. Continue sur plusieurs pages jusqu'à atteindre la limite cible

Version : Production (Basée sur les cartes + Pagination)
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from playwright.async_api import async_playwright


RAW_DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR.mkdir(exist_ok=True)


class UdemyScraper:
    """Scraper Udemy de production avec extraction par cartes et pagination."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def start(self):
        """Démarrer le navigateur avec une configuration furtive."""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        self.page = await self.context.new_page()
        await self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    async def stop(self):
        """Fermer le navigateur."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def search_and_scrape(self, search_query: str, limit: int = 70) -> List[Dict[str, Any]]:
        """
        Rechercher des cours et extraire les données avec pagination.
        
        Args:
            search_query: Sujet à rechercher
            limit: Nombre de cours à extraire (par défaut 70)
            
        Returns:
            Liste de dictionnaires contenant les cours
        """
        search_url = f"https://www.udemy.com/courses/search/?q={search_query.replace(' ', '+')}"
        
        print(f"\n[ÉTAPE 1] Navigation vers : {search_url}")
        await self.page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
        
        # Attendre le rendu JavaScript
        print(f"[ÉTAPE 2] Attente du rendu de la page...")
        await asyncio.sleep(8)
        
        # Faire défiler pour charger le contenu
        print(f"[ÉTAPE 3] Défilement pour charger le contenu...")
        for i in range(3):
            await self.page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1.5)
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        # Extraire les cours avec pagination
        print(f"[ÉTAPE 4] Extraction des cours avec pagination pour atteindre {limit} cours...")
        courses = await self.extract_courses_with_pagination(limit)
        
        print(f"\n[OK] {len(courses)} cours extraits avec succès")
        return courses
    
    async def extract_courses_with_pagination(self, limit: int) -> List[Dict[str, Any]]:
        """
        Extraire les cours en utilisant les sélecteurs avec support de la PAGINATION.
        Clique sur le lien 'Suivant' pour naviguer à travers les pages jusqu'à atteindre la limite.
        """
        courses = []
        seen_urls = set()
        page_number = 1
        no_new_content_count = 0
        
        while len(courses) < limit:
            print(f"\n[PAGE {page_number}] Actuel : {len(courses)}/{limit} cours")
            
            # Essayer de trouver les conteneurs de cartes de cours
            card_selectors = [
                'section[class*="course-product-card"]',
                'div.content-grid-item-module--item',
            ]
            
            cards = []
            for selector in card_selectors:
                cards = await self.page.query_selector_all(selector)
            if cards:
                    print(f"[OK] {len(cards)} cartes trouvées avec : {selector}")
                    break
            
            if not cards:
                print(f"[ERREUR] Aucune carte de cours trouvée sur la page {page_number} !")
                break
            
            # Traiter chaque carte sur la page actuelle
            new_courses_this_page = 0
            for i, card in enumerate(cards):
                if len(courses) >= limit:
                    break
                
                try:
                    course_data = await self.extract_from_card(card)
                    
                    if not course_data:
                        continue
                    
                    url = course_data.get("url")
                    if not url or url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    courses.append(course_data)
                    new_courses_this_page += 1
                    
                    # Affichage bref

                    title = course_data.get('title', 'N/A')[:50]
                    rating = course_data.get('rating', 'N/A')
                    print(f"  [{len(courses)}] {title} (Rating: {rating})")
                
                except Exception as e:
                    print(f"  [ERREUR] La carte {i+1} a échoué : {e}")
                    continue
            
            # Vérifier si nous avons de nouveaux cours
            if new_courses_this_page == 0:
                no_new_content_count += 1
                print(f"[ATTENTION] Pas de nouveaux cours sur la page {page_number} (essai {no_new_content_count}/3)")
                
                if no_new_content_count >= 3:
                    print(f"[ARRÊT] Pas de nouveau contenu après 3 pages. Arrêt.")
                    break
            else:
                no_new_content_count = 0
                print(f"[OK] Ajout de {new_courses_this_page} nouveaux cours depuis la page {page_number}")
            
            # Arrêter si nous en avons assez
            if len(courses) >= limit:
                print(f"[SUCCÈS] Objectif de {limit} cours atteint !")
                break
            
            # Essayer de trouver et cliquer sur le lien Suivant
            print(f"\n[ACTION] Recherche du lien Suivant...")
            
            # Défiler vers le bas pour s'assurer que la pagination est visible
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # IMPORTANT : Udemy utilise des balises <a> (liens), PAS des boutons !
            # Essayer plusieurs sélecteurs pour le lien Suivant
            next_element_selectors = [
                # Chercher des éléments <a> dans la pagination
                'nav[aria-label*="Pagination"] a:not([aria-disabled="true"]):last-of-type',
                'nav[aria-label="Pagination"] a[class*="next"]',
                'nav[aria-label="Pagination"] a:last-child:not([aria-disabled])',
                # Solution de repli vers les boutons si nécessaire

                'button[aria-label*="Next"]',
                'button[aria-label="Next page"]',
            ]
            
            next_element = None
            for selector in next_element_selectors:
                try:
                    next_element = await self.page.query_selector(selector)
                    if next_element:
                        # Vérifier si l'élément est désactivé
                        is_disabled = await next_element.get_attribute("aria-disabled")
                        if is_disabled != "true":  # Pas désactivé (vérifier la chaîne "true")
                            print(f"[OK] Lien Suivant trouvé avec : {selector}")
                            break
                        else:
                            next_element = None
                except Exception as e:
                    continue
            
            if not next_element:
                print(f"[ARRÊT] Aucun lien Suivant actif trouvé. Fin des résultats.")
                break
            
            # Cliquer sur l'élément Suivant (fonctionne pour <a> et <button>)
            print(f"[CLIC] Clic sur le lien Suivant...")
            try:
                await next_element.click()
                page_number += 1
                
                # Attendre le chargement de la nouvelle page
                print(f"[ATTENTE] Attente du chargement de la page {page_number}...")
                await asyncio.sleep(5)  # Attendre le chargement du nouveau contenu
                
                # Remonter en haut de la nouvelle page
                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERREUR] Échec du clic sur le lien Suivant : {e}")
                break
        
        return courses[:limit]
    
    async def extract_from_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Extraire les données d'une seule carte en utilisant DES SÉLECTEURS DIRECTS.
        
        Basé sur la structure HTML réelle :
        - Titre : h2 (PAS h3 !)
        - URL : a[href*="/course/"]
        - Instructeur : span[data-purpose*="visible-instructors"]
        - Note : span[data-purpose="rating-number"]
        - Autres données : ul.tag-list-module--list > li
        - Prix : div[data-purpose="course-price-text"]
        """
        try:
            data = {
                "platform": "Udemy",
                "scraped_at": datetime.now().isoformat()
            }
            
            # 1. TITRE - h2 (corrigé depuis h3 !)
            title_elem = await card.query_selector("h2 a div")
            if not title_elem:
                # Solution de repli : essayer juste h2
                title_elem = await card.query_selector("h2")
            
            if title_elem:
                data["title"] = (await title_elem.inner_text()).strip()
            else:
                data["title"] = "N/A"
            
            # 2. URL - a[href*="/course/"]
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
            instructor_elem = await card.query_selector('span[data-purpose*="visible-instructors"]')
            if instructor_elem:
                data["instructor"] = (await instructor_elem.inner_text()).strip()
            else:
                data["instructor"] = "N/A"
            
            # 4. RATING - span[data-purpose="rating-number"]
            rating_elem = await card.query_selector('span[data-purpose="rating-number"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                try:
                    data["rating"] = float(rating_text.strip())
                except:
                    data["rating"] = None
            else:
                data["rating"] = None
            
            # 5. EXTRAIRE DE LA LISTE DE TAGS - ul.tag-list-module--list
            # Cela inclut : avis, durée, cours, niveau
            tag_list = await card.query_selector('ul[class*="tag-list"]')
            if tag_list:
                tags_text = await tag_list.inner_text()
                
                # Parse tags
                import re
                
                # Avis : "22,772 ratings"
                reviews_match = re.search(r'([\d,]+)\s*ratings?', tags_text)
                if reviews_match:
                    data["reviews"] = int(reviews_match.group(1).replace(',', ''))
                else:
                    data["reviews"] = None
                
                # Durée : "99 total hours"
                duration_match = re.search(r'([\d.]+)\s*total hours?', tags_text)
                if duration_match:
                    data["duration_hours"] = float(duration_match.group(1))
                else:
                    data["duration_hours"] = None
                
                # Conférences : "429 lectures"
                lectures_match = re.search(r'(\d+)\s*lectures?', tags_text)
                if lectures_match:
                    data["lectures"] = int(lectures_match.group(1))
                else:
                    data["lectures"] = None
                
                # Niveau : "All Levels", "Beginner", etc.
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
            
            # 6. PRIX - div[data-purpose="course-price-text"]
            price_elem = await card.query_selector('div[data-purpose="course-price-text"]')
            if price_elem:
                price_text = await price_elem.inner_text()
                data["current_price"] = price_text.strip()
            else:
                data["current_price"] = "N/A"
            
            # 7. PRIX ORIGINAL - div[data-purpose="course-old-price-text"]
            original_price_elem = await card.query_selector('div[data-purpose="course-old-price-text"]')
            if original_price_elem:
                original_price_text = await original_price_elem.inner_text()
                data["original_price"] = original_price_text.strip()
            else:
                data["original_price"] = "N/A"
            
            # Note : Le nombre d'étudiants inscrits n'est PAS disponible sur les cartes de recherche
            data["students"] = None
            
            # Dernière mise à jour
            data["last_updated"] = None
            
            return data
        
        except Exception as e:
            print(f"    [ERREUR] Échec de l'extraction de la carte : {e}")
            return None


async def main():
    """Tester le scraper de production."""
    print("="*60)
    print("SCRAPER UDEMY V5 - PRODUCTION")
    print("="*60)
    print("\nFonctionnalités :")
    print("  - Extraction par cartes (sélecteurs h2, attributs data-purpose)")
    print("  - Pagination multi-page avec clic sur lien Suivant")
    print("  - Prévention des doublons")
    print("="*60)
    
    scraper = UdemyScraper(headless=False)
    
    try:
        await scraper.start()
        print("\nNavigateur démarré.")
        
        courses = await scraper.search_and_scrape("python", limit=5)
        
        if not courses:
            print("\n[ÉCHEC] Aucun cours extrait")
            print("[CONSEIL] Vérifiez que vous voyez les cours dans la fenêtre du navigateur")
            return
        
        # Enregistrer
        output_file = RAW_DATA_DIR / "udemy_v5_test.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(courses, f, indent=2, ensure_ascii=False)
        
        print(f"\n[ENREGISTRÉ] {len(courses)} cours")
        print(f"[FICHIER] {output_file.absolute()}")
        
        # Affichage
        for i, course in enumerate(courses, 1):
            print(f"\n[Cours {i}]")
            print(f"  Titre :       {course['title'][:60]}")
            print(f"  Instructeur : {course['instructor']}")
            print(f"  Note :        {course['rating']}")
            print(f"  Avis :        {course['reviews']}")
            print(f"  Étudiants :   {course['students']}")
            print(f"  Prix :        {course['current_price']}")
            print(f"  Durée :       {course['duration_hours']} heures" if course['duration_hours'] else "  Durée :       N/A")
            print(f"  Conférences : {course['lectures']}")
            print(f"  Niveau :      {course['level']}")
            print(f"  Mise à jour : {course['last_updated']}")
            print(f"  URL :         {course['url'][:60]}")
        
    except Exception as e:
        print(f"\nErreur : {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()
        print("\nNavigateur fermé.")


if __name__ == "__main__":
    asyncio.run(main())
