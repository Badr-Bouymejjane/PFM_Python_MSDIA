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

# === IMPORTATION DES BIBLIOTHÈQUES ===
import asyncio  # Programmation asynchrone (async/await)
import json  # Manipulation de fichiers JSON
from pathlib import Path  # Gestion moderne des chemins de fichiers
from typing import List, Dict, Any, Optional  # Annotations de types pour la clarté du code
from datetime import datetime  # Date et heure actuelles

from playwright.async_api import async_playwright  # Automatisation de navigateur

# === CONFIGURATION DU RÉPERTOIRE DE DONNÉES ===
# __file__ : chemin du fichier actuel
# .parent : répertoire parent (scrapers/)
# .parent.parent : répertoire grand-parent (Recommandations/)
RAW_DATA_DIR = Path(__file__).parent.parent / "data"  # Chemin vers le dossier data/
RAW_DATA_DIR.mkdir(exist_ok=True)  # Créer le dossier s'il n'existe pas (exist_ok=True : pas d'erreur si existe déjà)


# === CLASSE PRINCIPALE DU SCRAPER UDEMY ===
class UdemyScraper:
    """Scraper Udemy de production avec extraction par cartes et pagination."""
    
    def __init__(self, headless: bool = False):
        """Constructeur - initialise les attributs du scraper"""
        self.headless = headless  # Mode sans interface graphique (False = visible pour débogage)
        # Initialiser tous les attributs Playwright à None (seront créés dans start())
        self.browser = None  # Instance du navigateur
        self.context = None  # Contexte de navigation (environnement isolé)
        self.page = None  # Page web active
        self.playwright = None  # Instance Playwright principale
    
    async def start(self):
        """Démarrer le navigateur avec une configuration furtive (anti-détection)."""
        # Démarrer Playwright
        self.playwright = await async_playwright().start()
        
        # Lancer le navigateur Chromium avec options anti-détection
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,  # Mode visible ou invisible
            # Désactiver la fonctionnalité AutomationControlled qui signale qu'on est un bot
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Créer un contexte de navigation avec paramètres réalistes
        self.context = await self.browser.new_context(
            # User-Agent : identifiant du navigateur (simule un vrai navigateur Windows)
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},  # Résolution Full HD
            locale="en-US"  # Langue anglaise américaine
        )
        
        # Ouvrir une nouvelle page
        self.page = await self.context.new_page()
        # Injecter un script JavaScript pour masquer le fait qu'on utilise webdriver
        # Object.defineProperty : redéfinir une propriété de l'objet navigator
        # navigator.webdriver : propriété qui indique si on utilise l'automatisation
        await self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"  # Retourner undefined au lieu de true
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
            search_query: Sujet à rechercher (ex: "python", "machine learning")
            limit: Nombre de cours à extraire (par défaut 70)
            
        Returns:
            Liste de dictionnaires contenant les cours
        """
        # Construire l'URL de recherche Udemy
        # replace(' ', '+') : remplacer les espaces par + pour l'URL (ex: "machine learning" → "machine+learning")
        search_url = f"https://www.udemy.com/courses/search/?q={search_query.replace(' ', '+')}"
        
        print(f"\n[ÉTAPE 1] Navigation vers : {search_url}")
        # Naviguer vers l'URL avec timeout de 60 secondes
        # wait_until="domcontentloaded" : attendre que le DOM soit chargé (pas besoin d'attendre toutes les images)
        await self.page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
        
        # Attendre le rendu JavaScript (Udemy charge le contenu dynamiquement)
        print(f"[ÉTAPE 2] Attente du rendu de la page...")
        await asyncio.sleep(8)  # Attendre 8 secondes pour le chargement complet
        
        # Faire défiler pour charger le contenu (lazy loading)
        print(f"[ÉTAPE 3] Défilement pour charger le contenu...")
        for i in range(3):  # Défiler 3 fois
            # evaluate() : exécuter du JavaScript dans la page
            # scrollBy(x, y) : défiler de x pixels horizontalement et y verticalement
            await self.page.evaluate("window.scrollBy(0, 800)")  # Défiler de 800 pixels vers le bas
            await asyncio.sleep(1.5)  # Attendre 1.5 secondes entre chaque défilement
        # Remonter en haut de la page
        await self.page.evaluate("window.scrollTo(0, 0)")  # scrollTo(x, y) : aller à la position (0, 0)
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
        # === INITIALISATION DES VARIABLES ===
        courses = []  # Liste pour stocker les cours extraits
        seen_urls = set()  # Ensemble (set) pour tracker les URLs déjà vues (prévention des doublons)
        page_number = 1  # Compteur de pages
        no_new_content_count = 0  # Compteur de pages sans nouveau contenu
        
        # === BOUCLE PRINCIPALE DE PAGINATION ===
        # Continue tant qu'on n'a pas atteint la limite de cours
        while len(courses) < limit:
            print(f"\n[PAGE {page_number}] Actuel : {len(courses)}/{limit} cours")
            
            # === RECHERCHE DES CARTES DE COURS ===
            # Essayer de trouver les conteneurs de cartes de cours avec différents sélecteurs
            card_selectors = [
                'section[class*="course-product-card"]',  # Sélecteur principal (class contient "course-product-card")
                'div.content-grid-item-module--item',  # Sélecteur alternatif
            ]
            
            cards = []  # Liste pour stocker les cartes trouvées
            # Essayer chaque sélecteur jusqu'à trouver des cartes
            for selector in card_selectors:
                # query_selector_all() : trouve tous les éléments correspondant au sélecteur
                cards = await self.page.query_selector_all(selector)
            if cards:  # Si des cartes sont trouvées
                    print(f"[OK] {len(cards)} cartes trouvées avec : {selector}")
                    break  # Sortir de la boucle dès qu'on trouve des cartes
            
            # Si aucune carte n'est trouvée, arrêter le scraping
            if not cards:
                print(f"[ERREUR] Aucune carte de cours trouvée sur la page {page_number} !")
                break
            
            # === TRAITEMENT DE CHAQUE CARTE ===
            new_courses_this_page = 0  # Compteur de nouveaux cours sur cette page
            # enumerate() : boucle avec index (i) et élément (card)
            for i, card in enumerate(cards):
                # Vérifier si on a atteint la limite
                if len(courses) >= limit:
                    break  # Sortir de la boucle si limite atteinte
                
                try:
                    # Extraire les données de la carte
                    course_data = await self.extract_from_card(card)
                    
                    # Vérifier si l'extraction a réussi
                    if not course_data:
                        continue  # Passer à la carte suivante si échec
                    
                    # === PRÉVENTION DES DOUBLONS ===
                    url = course_data.get("url")  # Obtenir l'URL du cours
                    # Vérifier si l'URL existe et n'a pas déjà été vue
                    if not url or url in seen_urls:
                        continue  # Passer à la carte suivante si doublon
                    
                    # Ajouter l'URL à l'ensemble des URLs vues
                    seen_urls.add(url)  # set.add() : ajouter un élément à l'ensemble
                    courses.append(course_data)  # Ajouter le cours à la liste
                    new_courses_this_page += 1  # Incrémenter le compteur
                    
                    # Affichage bref du cours extrait
                    title = course_data.get('title', 'N/A')[:50]  # Titre tronqué à 50 caractères
                    rating = course_data.get('rating', 'N/A')
                    print(f"  [{len(courses)}] {title} (Rating: {rating})")
                
                except Exception as e:
                    # Capturer les erreurs et continuer avec la carte suivante
                    print(f"  [ERREUR] La carte {i+1} a échoué : {e}")
                    continue
            
            # === VÉRIFICATION DU PROGRÈS ===
            # Vérifier si nous avons de nouveaux cours sur cette page
            if new_courses_this_page == 0:
                no_new_content_count += 1  # Incrémenter le compteur de pages vides
                print(f"[ATTENTION] Pas de nouveaux cours sur la page {page_number} (essai {no_new_content_count}/3)")
                
                # Arrêter si pas de nouveau contenu pendant 3 pages consécutives
                if no_new_content_count >= 3:
                    print(f"[ARRÊT] Pas de nouveau contenu après 3 pages. Arrêt.")
                    break
            else:
                no_new_content_count = 0  # Réinitialiser le compteur si on trouve du contenu
                print(f"[OK] Ajout de {new_courses_this_page} nouveaux cours depuis la page {page_number}")
            
            # Vérifier si on a atteint l'objectif
            if len(courses) >= limit:
                print(f"[SUCCÈS] Objectif de {limit} cours atteint !")
                break
            
            # === NAVIGATION VERS LA PAGE SUIVANTE ===
            print(f"\n[ACTION] Recherche du lien Suivant...")
            
            # Défiler vers le bas pour s'assurer que la pagination est visible
            # document.body.scrollHeight : hauteur totale de la page
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)  # Attendre que la pagination soit visible
            
            # IMPORTANT : Udemy utilise des balises <a> (liens), PAS des boutons !
            # Liste de sélecteurs pour trouver le lien "Next"
            next_element_selectors = [
                # Chercher des éléments <a> dans la pagination
                # :not([aria-disabled="true"]) : exclure les liens désactivés
                # :last-of-type : prendre le dernier lien (généralement "Next")
                'nav[aria-label*="Pagination"] a:not([aria-disabled="true"]):last-of-type',
                'nav[aria-label="Pagination"] a[class*="next"]',  # Lien avec class contenant "next"
                'nav[aria-label="Pagination"] a:last-child:not([aria-disabled])',  # Dernier enfant non désactivé
                # Solution de repli vers les boutons si nécessaire
                'button[aria-label*="Next"]',  # Bouton avec aria-label contenant "Next"
                'button[aria-label="Next page"]',  # Bouton avec aria-label exact
            ]
            
            next_element = None  # Variable pour stocker le lien trouvé
            # Essayer chaque sélecteur
            for selector in next_element_selectors:
                try:
                    # query_selector() : trouve le premier élément correspondant
                    next_element = await self.page.query_selector(selector)
                    if next_element:
                        # Vérifier si l'élément est désactivé
                        # get_attribute() : obtenir la valeur d'un attribut HTML
                        is_disabled = await next_element.get_attribute("aria-disabled")
                        if is_disabled != "true":  # Pas désactivé (vérifier la chaîne "true")
                            print(f"[OK] Lien Suivant trouvé avec : {selector}")
                            break  # Sortir de la boucle si lien valide trouvé
                        else:
                            next_element = None  # Réinitialiser si désactivé
                except Exception as e:
                    continue  # Ignorer les erreurs et essayer le sélecteur suivant
            
            # Si aucun lien "Next" actif n'est trouvé, arrêter
            if not next_element:
                print(f"[ARRÊT] Aucun lien Suivant actif trouvé. Fin des résultats.")
                break
            
            # === CLIC SUR LE LIEN SUIVANT ===
            # Cliquer sur l'élément Suivant (fonctionne pour <a> et <button>)
            print(f"[CLIC] Clic sur le lien Suivant...")
            try:
                await next_element.click()  # Cliquer sur l'élément
                page_number += 1  # Incrémenter le numéro de page
                
                # Attendre le chargement de la nouvelle page
                print(f"[ATTENTE] Attente du chargement de la page {page_number}...")
                await asyncio.sleep(5)  # Attendre 5 secondes pour le chargement du nouveau contenu
                
                # Remonter en haut de la nouvelle page
                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[ERREUR] Échec du clic sur le lien Suivant : {e}")
                break  # Arrêter en cas d'erreur
        
        # Retourner les cours (limités au nombre demandé)
        # [:limit] : slice pour prendre seulement les 'limit' premiers éléments
        return courses[:limit]
    
    async def extract_from_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Extraire les données d'une seule carte en utilisant DES SÉLECTEURS DIRECTS.
        
        Basé sur la structure HTML réelle d'Udemy :
        - Titre : h2 (PAS h3 !)
        - URL : a[href*="/course/"]
        - Instructeur : span[data-purpose*="visible-instructors"]
        - Note : span[data-purpose="rating-number"]
        - Autres données : ul.tag-list-module--list > li
        - Prix : div[data-purpose="course-price-text"]
        """
        try:
            # === INITIALISATION DU DICTIONNAIRE ===
            data = {
                "platform": "Udemy",  # Nom de la plateforme
                "scraped_at": datetime.now().isoformat()  # Date/heure d'extraction au format ISO
            }
            
            # === 1. EXTRACTION DU TITRE (h2) ===
            # IMPORTANT : Udemy utilise h2, pas h3 !
            title_elem = await card.query_selector("h2 a div")  # Titre dans un div à l'intérieur d'un lien dans h2
            if not title_elem:
                # Solution de repli : essayer juste h2 si la structure est différente
                title_elem = await card.query_selector("h2")
            
            if title_elem:
                # inner_text() : obtenir le texte visible de l'élément
                # strip() : supprimer les espaces au début et à la fin
                data["title"] = (await title_elem.inner_text()).strip()
            else:
                data["title"] = "N/A"  # Valeur par défaut si non trouvé
            
            # === 2. EXTRACTION DE L'URL (CRITIQUE) ===
            # Chercher un lien contenant "/course/" dans l'attribut href
            # [href*="/course/"] : sélecteur CSS pour attribut contenant une chaîne
            url_elem = await card.query_selector('a[href*="/course/"]')
            if url_elem:
                # get_attribute() : obtenir la valeur d'un attribut HTML
                url = await url_elem.get_attribute("href")
                if url:
                    # Vérifier si l'URL est relative ou absolue
                    if not url.startswith("http"):
                        # Construire l'URL complète si relative
                        url = f"https://www.udemy.com{url}"
                    data["url"] = url
                else:
                    return None  # Retourner None si pas d'URL (cours invalide)
            else:
                return None  # CRITIQUE : sans URL, le cours n'est pas valide
            
            # === 3. EXTRACTION DE L'INSTRUCTEUR ===
            # Utiliser l'attribut data-purpose pour cibler précisément l'élément
            # [data-purpose*="visible-instructors"] : attribut contenant "visible-instructors"
            instructor_elem = await card.query_selector('span[data-purpose*="visible-instructors"]')
            if instructor_elem:
                data["instructor"] = (await instructor_elem.inner_text()).strip()
            else:
                data["instructor"] = "N/A"  # Valeur par défaut
            
            # === 4. EXTRACTION DE LA NOTE (RATING) ===
            # Utiliser data-purpose pour cibler l'élément exact contenant la note
            rating_elem = await card.query_selector('span[data-purpose="rating-number"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                try:
                    # Convertir le texte en nombre décimal (float)
                    data["rating"] = float(rating_text.strip())
                except:
                    data["rating"] = None  # None si conversion échoue
            else:
                data["rating"] = None
            
            # === 5. EXTRACTION DE LA LISTE DE TAGS ===
            # La liste de tags contient : avis, durée, nombre de lectures, niveau
            # Chercher l'élément ul avec class contenant "tag-list"
            tag_list = await card.query_selector('ul[class*="tag-list"]')
            if tag_list:
                # Obtenir tout le texte de la liste de tags
                tags_text = await tag_list.inner_text()
                
                # Importer le module regex (déjà importé en haut, mais explicité ici pour clarté)
                import re
                
                # === EXTRACTION DES AVIS (REVIEWS) ===
                # Pattern regex : "22,772 ratings" ou "150 rating"
                # ([\d,]+) : capture un ou plusieurs chiffres avec virgules optionnelles
                # \s* : espaces optionnels
                # ratings? : "rating" ou "ratings" (s optionnel avec ?)
                reviews_match = re.search(r'([\d,]+)\s*ratings?', tags_text)
                if reviews_match:
                    # Extraire le nombre et supprimer les virgules
                    # replace(',', '') : supprimer toutes les virgules
                    # int() : convertir en entier
                    data["reviews"] = int(reviews_match.group(1).replace(',', ''))
                else:
                    data["reviews"] = None
                
                # === EXTRACTION DE LA DURÉE ===
                # Pattern : "99 total hours" ou "5.5 total hours"
                # ([\d.]+) : capture chiffres avec point décimal optionnel
                duration_match = re.search(r'([\d.]+)\s*total hours?', tags_text)
                if duration_match:
                    # Convertir en nombre décimal (float)
                    data["duration_hours"] = float(duration_match.group(1))
                else:
                    data["duration_hours"] = None
                
                # === EXTRACTION DU NOMBRE DE LECTURES ===
                # Pattern : "429 lectures" ou "50 lecture"
                # (\d+) : capture un ou plusieurs chiffres (sans virgule ni décimale)
                lectures_match = re.search(r'(\d+)\s*lectures?', tags_text)
                if lectures_match:
                    data["lectures"] = int(lectures_match.group(1))
                else:
                    data["lectures"] = None
                
                # === EXTRACTION DU NIVEAU ===
                # Liste des niveaux possibles sur Udemy
                level_keywords = ['All Levels', 'Beginner', 'Intermediate', 'Advanced', 'Expert']
                data["level"] = "N/A"  # Valeur par défaut
                # Chercher chaque mot-clé dans le texte
                for keyword in level_keywords:
                    if keyword in tags_text:  # Vérifier si le mot-clé est présent
                        data["level"] = keyword
                        break  # Sortir dès qu'un niveau est trouvé
            else:
                # Si pas de liste de tags, mettre toutes les valeurs à None
                data["reviews"] = None
                data["duration_hours"] = None
                data["lectures"] = None
                data["level"] = "N/A"
            
            # === 6. EXTRACTION DU PRIX ACTUEL ===
            # Utiliser data-purpose pour cibler l'élément du prix
            price_elem = await card.query_selector('div[data-purpose="course-price-text"]')
            if price_elem:
                price_text = await price_elem.inner_text()
                data["current_price"] = price_text.strip()  # Prix actuel (ex: "$13.99")
            else:
                data["current_price"] = "N/A"
            
            # === 7. EXTRACTION DU PRIX ORIGINAL ===
            # Prix barré (prix avant réduction)
            original_price_elem = await card.query_selector('div[data-purpose="course-old-price-text"]')
            if original_price_elem:
                original_price_text = await original_price_elem.inner_text()
                data["original_price"] = original_price_text.strip()  # Prix original (ex: "$84.99")
            else:
                data["original_price"] = "N/A"  # Pas de prix original (pas de réduction)
            
            # === INFORMATIONS NON DISPONIBLES SUR LES CARTES ===
            # Note : Le nombre d'étudiants inscrits n'est PAS disponible sur les cartes de recherche
            # Il faudrait visiter la page individuelle du cours pour obtenir cette info
            data["students"] = None
            
            # Dernière mise à jour du cours (non disponible sur les cartes)
            data["last_updated"] = None
            
            return data  # Retourner le dictionnaire complet avec toutes les données
        
        except Exception as e:
            # Capturer toute erreur et afficher un message
            print(f"    [ERREUR] Échec de l'extraction de la carte : {e}")
            return None  # Retourner None en cas d'erreur


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
