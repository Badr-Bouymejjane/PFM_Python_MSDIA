import asyncio
import random
import pandas as pd
import json
from playwright.async_api import async_playwright
from datetime import datetime
from config import *

# ---------------------------------------
# DONNÉES GLOBALES
# ---------------------------------------
all_data = []

# ---------------------------------------
# FONCTION DE SCRAPING
# ---------------------------------------
async def scrape_domain(page, domain, domain_index, total_domains):
    """Scrape tous les cours d'un domaine spécifique"""
    
    url = f"https://www.coursera.org/search?query={domain.replace(' ', '%20')}"
    
    print("\n" + "="*70)
    print(f"🎯 DOMAINE {domain_index}/{total_domains}: {domain.upper()}")
    print("="*70)
    
    print(f"🌐 Navigation vers: {url}")
    await page.goto(url, timeout=PAGE_TIMEOUT)
    
    # Attente chargement dynamique
    print("⏳ Attente du chargement initial...")
    await page.wait_for_timeout(random.randint(5000, 7000))
    
    # Scroll progressif pour charger plus de cours
    print(f"📜 Scroll progressif ({NUM_SCROLLS} scrolls)...")
    for i in range(NUM_SCROLLS):
        await page.mouse.wheel(0, random.randint(1200, 1800))
        await page.wait_for_timeout(random.randint(2000, 4000))
        print(f"   Scroll {i+1}/{NUM_SCROLLS}")
    
    # Attente supplémentaire pour le chargement
    await page.wait_for_timeout(3000)
    
    # Trouver les cartes de cours
    print("\n🔍 Recherche des cartes de cours...")
    
    selectors = [
        "li.cds-9.css-0.cds-11.cds-grid-item",
        "li[data-testid='search-result-card']",
        "div[data-testid='search-result-card']",
    ]
    
    courses = None
    used_selector = None
    
    for selector in selectors:
        temp_courses = page.locator(selector)
        count = await temp_courses.count()
        if count > 0:
            courses = temp_courses
            used_selector = selector
            print(f"✅ Sélecteur trouvé: {selector}")
            break
    
    if courses is None or await courses.count() == 0:
        print(f"❌ Aucun cours trouvé pour '{domain}'")
        return []
    
    total_courses = await courses.count()
    courses_to_scrape = min(total_courses, MAX_COURSES_PER_DOMAIN) if MAX_COURSES_PER_DOMAIN else total_courses
    
    print(f"📊 {total_courses} cours détectés, extraction de {courses_to_scrape} cours")
    
    domain_data = []
    
    for i in range(courses_to_scrape):
        course = courses.nth(i)
        
        # Affichage de progression
        if (i + 1) % 10 == 0 or i == 0:
            print(f"📘 Extraction: {i+1}/{courses_to_scrape}")
        
        async def safe_text(locator):
            try:
                text = await locator.inner_text(timeout=2000)
                if text:
                    return text.strip()
                return None
            except:
                return None
        
        # TITRE
        title = None
        try:
            loc = course.locator("h3.cds-CommonCard-title").first
            if await loc.count() > 0:
                title = await safe_text(loc)
        except:
            pass
        
        # ORGANISATION
        organization = None
        try:
            loc = course.locator("p.cds-ProductCard-partnerNames").first
            if await loc.count() > 0:
                organization = await safe_text(loc)
        except:
            pass
        
        # RATING
        rating = None
        try:
            loc = course.locator("span.css-4s48ix").first
            if await loc.count() > 0:
                rating = await safe_text(loc)
                if rating == "·":
                    rating = None
        except:
            pass
        
        # REVIEWS
        reviews = None
        try:
            footer = course.locator("div.cds-ProductCard-footer").first
            if await footer.count() > 0:
                review_divs = footer.locator("div.css-vac8rf")
                review_count = await review_divs.count()
                for j in range(review_count):
                    text = await safe_text(review_divs.nth(j))
                    if text and ("avis" in text.lower() or "k" in text.lower()):
                        reviews = text
                        break
        except:
            pass
        
        # METADATA (Level, Type, Duration)
        level = None
        course_type = None
        duration = None
        try:
            metadata = course.locator("div.cds-CommonCard-metadata").first
            if await metadata.count() > 0:
                level_p = metadata.locator("p.css-vac8rf").first
                if await level_p.count() > 0:
                    metadata_text = await safe_text(level_p)
                    if metadata_text:
                        # Split by '·' separator
                        parts = [part.strip() for part in metadata_text.split('·')]
                        if len(parts) >= 3:
                            level = parts[0]
                            course_type = parts[1]
                            duration = parts[2]
                        elif len(parts) == 2:
                            level = parts[0]
                            course_type = parts[1]
                        elif len(parts) == 1:
                            level = parts[0]
        except:
            pass
        
        # URL du cours
        course_url = None
        try:
            link = course.locator("a.cds-CommonCard-titleLink").first
            if await link.count() > 0:
                href = await link.get_attribute("href")
                if href:
                    course_url = f"https://www.coursera.org{href}" if href.startswith("/") else href
        except:
            pass
        
        domain_data.append({
            "domain": domain,
            "title": title,
            "organization": organization,
            "rating": rating,
            "reviews": reviews,
            "level": level,
            "course_type": course_type,
            "duration": duration,
            "url": course_url
        })
        
        # Pause humaine aléatoire
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    print(f"✅ {len(domain_data)} cours extraits pour '{domain}'")
    
    return domain_data


async def scrape_all_domains():
    """Scrape tous les domaines configurés"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS_MODE,
            slow_mo=SLOW_MO
        )
        
        context = await browser.new_context(
            user_agent=USER_AGENT
        )
        
        page = await context.new_page()
        
        total_domains = len(DOMAINS)
        
        print("\n" + "🚀"*35)
        print(f"🎓 SCRAPING COURSERA - {total_domains} DOMAINES")
        print("🚀"*35)
        
        for idx, domain in enumerate(DOMAINS, 1):
            try:
                domain_data = await scrape_domain(page, domain, idx, total_domains)
                
                if domain_data:
                    all_data.extend(domain_data)
                
                # Pause entre domaines (sauf pour le dernier)
                if idx < total_domains:
                    print(f"\n⏸️  Pause de {PAUSE_BETWEEN_DOMAINS}s avant le prochain domaine...")
                    await asyncio.sleep(PAUSE_BETWEEN_DOMAINS)
                
            except Exception as e:
                print(f"\n❌ Erreur lors du scraping de '{domain}': {e}")
                continue
        
        await browser.close()


# ---------------------------------------
# POINT D'ENTRÉE
# ---------------------------------------
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 COURSERA MULTI-DOMAIN SCRAPER")
    print("="*70)
    print(f"📚 Domaines à scraper: {len(DOMAINS)}")
    print(f"📊 Cours max par domaine: {MAX_COURSES_PER_DOMAIN if MAX_COURSES_PER_DOMAIN else 'Illimité'}")
    print(f"📜 Nombre de scrolls: {NUM_SCROLLS}")
    print(f"💾 Fichier CSV: {OUTPUT_FILE}")
    if SAVE_JSON:
        print(f"💾 Fichier JSON: {JSON_OUTPUT_FILE}")
    print("="*70)
    
    start_time = datetime.now()
    
    # Lancer le scraping
    asyncio.run(scrape_all_domains())
    
    # Sauvegarder les données
    if all_data:
        df_new = pd.DataFrame(all_data)
        
        # Charger les données existantes si le fichier existe
        try:
            df_existing = pd.read_csv(OUTPUT_FILE, encoding="utf-8")
            print(f"\n📂 Données existantes chargées: {len(df_existing)} cours")
            # Combiner les anciennes et nouvelles données
            df = pd.concat([df_existing, df_new], ignore_index=True)
            print(f"➕ Nouvelles données ajoutées: {len(df_new)} cours")
            print(f"📊 Total après fusion: {len(df)} cours")
        except FileNotFoundError:
            print(f"\n📝 Nouveau fichier CSV créé")
            df = df_new
        
        # Sauvegarder en CSV
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
        print(f"✅ Fichier CSV sauvegardé: {OUTPUT_FILE}")
        
        # Sauvegarder en JSON si configuré
        if SAVE_JSON:
            with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Fichier JSON sauvegardé: {JSON_OUTPUT_FILE}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "🎉"*35)
        print("✅ SCRAPING TERMINÉ AVEC SUCCÈS!")
        print("🎉"*35)
        print(f"\n📊 Statistiques:")
        print(f"   • Total de cours extraits: {len(all_data)}")
        print(f"   • Domaines scrapés: {df['domain'].nunique()}")
        print(f"   • Durée totale: {duration:.0f} secondes ({duration/60:.1f} minutes)")
        
        print(f"\n📋 Répartition par domaine:")
        domain_counts = df['domain'].value_counts()
        for domain, count in domain_counts.items():
            print(f"   • {domain}: {count} cours")
        
        print(f"\n💡 Qualité des données:")
        print(f"   • Cours avec rating: {df['rating'].notna().sum()} ({df['rating'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   • Cours avec reviews: {df['reviews'].notna().sum()} ({df['reviews'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   • Cours avec level: {df['level'].notna().sum()} ({df['level'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   • Cours avec course_type: {df['course_type'].notna().sum()} ({df['course_type'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   • Cours avec duration: {df['duration'].notna().sum()} ({df['duration'].notna().sum()/len(df)*100:.1f}%)")
        print(f"   • Cours avec URL: {df['url'].notna().sum()} ({df['url'].notna().sum()/len(df)*100:.1f}%)")
        
        print(f"\n📈 Aperçu des 10 premiers cours:")
        print(df.head(10).to_string())
        
    else:
        print("\n❌ Aucune donnée extraite")
