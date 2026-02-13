"""
Scraper Coursera - Extraire les cours de Coursera
Utilise Playwright pour le chargement de contenu dynamique
"""

# === IMPORTATION DES MODULES SYSTÈME ===
import sys  # Module système pour accéder aux paramètres Python
import os   # Module pour interagir avec le système d'exploitation (fichiers, chemins)
# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === IMPORTATION DES BIBLIOTHÈQUES PRINCIPALES ===
import asyncio  # Bibliothèque pour la programmation asynchrone (async/await)
import pandas as pd  # Bibliothèque pour la manipulation de données (DataFrames, CSV)
from datetime import datetime  # Pour obtenir la date et l'heure actuelles
from playwright.async_api import async_playwright  # Automatisation de navigateur pour contenu dynamique
import re  # Module pour les expressions régulières (recherche de patterns dans le texte)
import time  # Module pour gérer le temps et les pauses

# === IMPORTATION DE LA CONFIGURATION ===
# Essayer d'importer les paramètres depuis le fichier config.py
try:
    from config import CATEGORIES, MAX_COURSES_PER_CATEGORY, HEADLESS_MODE, REQUEST_DELAY
except ImportError:
    # Si le fichier config.py n'existe pas, utiliser des valeurs par défaut
    CATEGORIES = ['data-science', 'machine-learning', 'python']  # Catégories à scraper
    MAX_COURSES_PER_CATEGORY = 30  # Nombre maximum de cours par catégorie
    HEADLESS_MODE = True  # Mode sans interface graphique (True = invisible)
    REQUEST_DELAY = 2  # Délai en secondes entre les requêtes (évite la surcharge)


# === CLASSE PRINCIPALE DU SCRAPER COURSERA ===
class CourseraScraper:
    """Scraper pour Coursera utilisant Playwright"""
    
    # Attributs de classe (partagés par toutes les instances)
    BASE_URL = "https://www.coursera.org"  # URL de base du site Coursera
    SEARCH_URL = "https://www.coursera.org/search?query={query}"  # Template d'URL de recherche
    
    def __init__(self, headless=True):
        """Constructeur de la classe - initialise une nouvelle instance du scraper"""
        self.headless = headless  # Mode d'affichage du navigateur (True = invisible)
        self.courses = []  # Liste vide pour stocker les cours extraits
        
    async def init_browser(self):
        """Initialise le navigateur Playwright"""
        # Démarrer Playwright (async = opération asynchrone, await = attendre la fin)
        self.playwright = await async_playwright().start()
        # Lancer le navigateur Chromium (headless = sans interface graphique si True)
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        # Créer un contexte de navigation (environnement isolé avec ses propres cookies/cache)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},  # Résolution de la fenêtre (Full HD)
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'  # Simule un navigateur réel
        )
        # Ouvrir une nouvelle page dans le contexte
        self.page = await self.context.new_page()
        
    async def close_browser(self):
        """Ferme le navigateur"""
        await self.browser.close()
        await self.playwright.stop()
        
    async def handle_cookie_consent(self):
        """Gère le popup de consentement cookies"""
        try:
            # Liste de sélecteurs CSS pour trouver le bouton d'acceptation des cookies
            consent_selectors = [
                'button:has-text("Accept")',  # Bouton contenant le texte "Accept"
                'button:has-text("Accepter")',  # Version française
                'button[data-testid="accept-cookies"]',  # Bouton avec attribut data-testid
                '#onetrust-accept-btn-handler'  # ID spécifique du bouton OneTrust
            ]
            # Essayer chaque sélecteur jusqu'à trouver le bouton
            for selector in consent_selectors:
                try:
                    btn = self.page.locator(selector)  # Localiser l'élément
                    if await btn.count() > 0:  # Vérifier si l'élément existe
                        await btn.first.click()  # Cliquer sur le premier élément trouvé
                        await asyncio.sleep(1)  # Attendre 1 seconde après le clic
                        break  # Sortir de la boucle si succès
                except:
                    pass  # Ignorer les erreurs et essayer le sélecteur suivant
        except:
            pass  # Ignorer si aucun popup de cookies n'est trouvé
            
    async def scroll_page(self, scroll_count=5):
        """Fait défiler la page pour charger plus de contenu (lazy loading)"""
        # Boucle pour défiler plusieurs fois (scroll_count = nombre de défilements)
        for _ in range(scroll_count):
            # Exécuter du JavaScript dans la page pour défiler d'une hauteur d'écran
            # window.scrollBy(x, y) : défiler de x pixels horizontalement et y verticalement
            # window.innerHeight : hauteur de la fenêtre du navigateur
            await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(1)  # Attendre 1 seconde pour laisser le contenu se charger
            
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
        # Créer un dictionnaire pour stocker les informations du cours
        course = {
            'platform': 'Coursera',  # Nom de la plateforme
            'category': category.replace('-', ' ').title(),  # Catégorie formatée (ex: 'data-science' → 'Data Science')
            'scraped_at': datetime.now().isoformat()  # Date/heure d'extraction au format ISO (ex: '2026-02-12T10:30:00')
        }
        
        # === EXTRACTION DU TITRE ===
        # Liste de sélecteurs CSS possibles pour trouver le titre (essayer dans l'ordre)
        title_selectors = ['h3', 'h2', '[data-testid="product-card-title"]', '.product-name']
        for sel in title_selectors:
            try:
                elem = card.locator(sel)  # Chercher l'élément dans la carte
                if await elem.count() > 0:  # Vérifier si l'élément existe
                    course['title'] = await elem.first.inner_text()  # Extraire le texte du premier élément
                    break  # Sortir de la boucle dès qu'on trouve le titre
            except:
                pass  # Ignorer les erreurs et essayer le sélecteur suivant
                
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
                
        # === EXTRACTION DE LA NOTE (RATING) ===
        # Chercher les éléments contenant la note du cours
        rating_selectors = ['[aria-label*="rating"]', 'span:has-text("stars")', '.ratings-text']
        for sel in rating_selectors:
            try:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    text = await elem.first.inner_text()  # Obtenir le texte (ex: "4.8 stars")
                    # Utiliser une expression régulière pour extraire le nombre
                    # r'(\d+[.,]?\d*)' : cherche un nombre avec ou sans décimales
                    match = re.search(r'(\d+[.,]?\d*)', text)
                    if match:
                        # Convertir en float (remplacer virgule par point pour format anglais)
                        course['rating'] = float(match.group(1).replace(',', '.'))
                    break
            except:
                pass
                
        # === EXTRACTION DU NOMBRE DE REVIEWS ===
        try:
            text = await card.inner_text()  # Obtenir tout le texte de la carte
            # Regex pour trouver le nombre de reviews (ex: "22,772 reviews" ou "150K students")
            # \(? : parenthèse optionnelle, [\d.,]+ : nombre avec virgules/points
            # [KkMm]? : suffixe K ou M optionnel, re.I : ignorer la casse
            review_match = re.search(r'\(?([\d.,]+)\s*[KkMm]?\)?\s*(?:reviews?|avis|étudiants?|students?)', text, re.I)
            if review_match:
                num_str = review_match.group(1).replace(',', '.')  # Extraire le nombre
                num = float(num_str)
                # Gérer les suffixes K (milliers) et M (millions)
                if 'k' in text.lower():
                    num *= 1000  # Multiplier par 1000 si K
                elif 'm' in text.lower():
                    num *= 1000000  # Multiplier par 1 million si M
                course['num_reviews'] = int(num)  # Convertir en entier
        except:
            pass  # Ignorer si non trouvé
            
        # === EXTRACTION DU NIVEAU DU COURS ===
        # Dictionnaire de mots-clés pour identifier le niveau
        level_keywords = {
            'Beginner': ['débutant', 'beginner', 'introduct', 'basic'],  # Mots pour niveau débutant
            'Intermediate': ['intermédiaire', 'intermediate', 'medium'],  # Mots pour niveau intermédiaire
            'Advanced': ['avancé', 'advanced', 'expert', 'professional']  # Mots pour niveau avancé
        }
        
        try:
            text = await card.inner_text()  # Obtenir tout le texte de la carte
            text_lower = text.lower()  # Convertir en minuscules pour comparaison
            # Parcourir chaque niveau et ses mots-clés
            for level, keywords in level_keywords.items():
                # Vérifier si un des mots-clés est présent dans le texte
                # any() : retourne True si au moins un élément est True
                if any(kw in text_lower for kw in keywords):
                    course['level'] = level  # Assigner le niveau trouvé
                    break  # Sortir de la boucle dès qu'un niveau est trouvé
        except:
            pass  # Ignorer si le niveau n'est pas trouvé
            
        # === EXTRACTION DU PRIX ===
        try:
            text = await card.inner_text()  # Obtenir le texte de la carte
            # Vérifier si le cours est gratuit (mots "free" ou "gratuit")
            if 'free' in text.lower() or 'gratuit' in text.lower():
                course['price'] = 'Free'  # Marquer comme gratuit
            else:
                # Chercher un prix avec symbole monétaire (ex: "$49.99", "€29.99")
                # [\$€£] : symboles de devises, \s* : espaces optionnels
                # \d+(?:[.,]\d{2})? : nombre avec optionnellement 2 décimales
                price_match = re.search(r'[\$€£]\s*(\d+(?:[.,]\d{2})?)', text)
                if price_match:
                    course['price'] = price_match.group(0)  # Extraire le prix complet avec symbole
                else:
                    course['price'] = 'Subscription'  # Si pas de prix, c'est probablement un abonnement
        except:
            pass  # Ignorer si le prix n'est pas trouvé
            
        # === EXTRACTION DE L'URL DU COURS ===
        try:
            link = card.locator('a').first  # Trouver le premier lien <a> dans la carte
            if await link.count() > 0:  # Vérifier que le lien existe
                href = await link.get_attribute('href')  # Obtenir l'attribut href du lien
                if href:
                    # Vérifier si l'URL est relative (commence par /) ou absolue
                    if href.startswith('/'):
                        course['url'] = self.BASE_URL + href  # Construire l'URL complète
                    else:
                        course['url'] = href  # Utiliser l'URL telle quelle
        except:
            pass  # Ignorer si l'URL n'est pas trouvée
            
        # === EXTRACTION DE LA DESCRIPTION ===
        try:
            # Chercher les paragraphes qui ne sont pas le nom de l'organisation
            desc_selectors = ['p:not(.cds-ProductCard-partnerNames)', '.description']
            for sel in desc_selectors:
                elem = card.locator(sel)
                if await elem.count() > 0:
                    course['description'] = await elem.first.inner_text()
                    break
        except:
            # Si pas de description, utiliser le titre comme description par défaut
            course['description'] = course.get('title', '')
            
        # === INFORMATIONS SUPPLÉMENTAIRES ===
        # Compétences : utiliser la catégorie comme compétences (remplacer - par ,)
        course['skills'] = category.replace('-', ', ')
        # Langue : par défaut anglais (Coursera est principalement en anglais)
        course['language'] = 'English'
        
        return course  # Retourner le dictionnaire contenant toutes les données du cours
        
    async def scrape_all(self, categories=None, max_per_category=30):
        """Scrape toutes les catégories"""
        # Si aucune catégorie n'est fournie, utiliser celles de la configuration
        if categories is None:
            categories = CATEGORIES
            
        # Afficher le header du programme
        print("\n" + "="*60)
        print("   SCRAPER COURSERA")
        print("="*60)
        
        # Initialiser le navigateur Playwright
        await self.init_browser()
        
        all_courses = []  # Liste pour stocker tous les cours de toutes les catégories
        # Boucle sur chaque catégorie avec enumerate pour avoir l'index
        for i, category in enumerate(categories):
            print(f"\n[{i+1}/{len(categories)}] Catégorie: {category}")
            # Scraper la catégorie actuelle
            courses = await self.scrape_category(category, max_per_category)
            # Ajouter les cours de cette catégorie à la liste totale
            # extend() : ajoute tous les éléments d'une liste à une autre
            all_courses.extend(courses)
            # Attendre REQUEST_DELAY secondes avant la prochaine catégorie (évite la surcharge)
            await asyncio.sleep(REQUEST_DELAY)
            
        # Fermer le navigateur après avoir terminé
        await self.close_browser()
        
        # Stocker les cours dans l'attribut de l'instance
        self.courses = all_courses
        print(f"\n✅ Total: {len(all_courses)} cours scrapés de Coursera")
        
        return all_courses  # Retourner la liste complète des cours
        
    def to_dataframe(self):
        """Convertit les cours en DataFrame Pandas"""
        # pd.DataFrame() : crée un tableau structuré à partir d'une liste de dictionnaires
        # Chaque dictionnaire devient une ligne, les clés deviennent les colonnes
        return pd.DataFrame(self.courses)
        
    def save_to_csv(self, filepath):
        """Sauvegarde les cours dans un fichier CSV"""
        df = self.to_dataframe()  # Convertir en DataFrame
        # to_csv() : exporte le DataFrame en fichier CSV
        # index=False : ne pas inclure l'index des lignes
        # encoding='utf-8' : utiliser l'encodage UTF-8 pour supporter les caractères spéciaux
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
