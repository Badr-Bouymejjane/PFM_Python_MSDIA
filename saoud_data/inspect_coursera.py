import asyncio
from playwright.async_api import async_playwright

# Script pour inspecter la structure HTML d'une carte de cours Coursera

async def inspect_coursera():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=60
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120 Safari/537.36"
            )
        )

        page = await context.new_page()
        url = "https://www.coursera.org/search?query=data%20science"
        
        print(f"🌐 Navigation vers: {url}")
        await page.goto(url, timeout=60000)
        
        print("⏳ Attente du chargement...")
        await page.wait_for_timeout(8000)
        
        # Scroll
        print("📜 Scroll...")
        for i in range(2):
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(2000)
        
        # Trouver les cartes de cours
        print("\n🔍 Recherche des cartes de cours...")
        
        selectors = [
            "li[data-testid='search-result-card']",
            "div[data-testid='search-result-card']",
            "li.cds-9.css-0.cds-11.cds-grid-item",
            "div.cds-ProductCard-container",
            "li[class*='search-result']",
            "div[class*='ProductCard']",
            "li.cds-ProductCard-gridCard"
        ]
        
        courses = None
        used_selector = None
        
        for selector in selectors:
            temp_courses = page.locator(selector)
            count = await temp_courses.count()
            print(f"   '{selector}': {count} éléments")
            if count > 0:
                courses = temp_courses
                used_selector = selector
                break
        
        if courses is None or await courses.count() == 0:
            print("❌ Aucune carte trouvée")
            await page.screenshot(path="debug_no_cards.png")
            await browser.close()
            return
        
        print(f"\n✅ Utilisation du sélecteur: {used_selector}")
        print(f"📊 {await courses.count()} cartes trouvées\n")
        
        # Inspecter la première carte en détail
        first_card = courses.first
        
        print("="*60)
        print("🔍 INSPECTION DE LA PREMIÈRE CARTE")
        print("="*60)
        
        # Obtenir le HTML complet de la première carte
        html = await first_card.inner_html()
        
        print("\n📄 HTML de la carte:")
        print("-"*60)
        print(html[:2000])  # Premiers 2000 caractères
        print("-"*60)
        
        # Sauvegarder le HTML complet
        with open("first_card.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n💾 HTML complet sauvegardé dans: first_card.html")
        
        # Essayer de trouver tous les spans, divs, p dans la carte
        print("\n🔍 Analyse des éléments dans la carte:")
        print("-"*60)
        
        # Tous les textes visibles
        all_text = await first_card.inner_text()
        print("\n📝 Texte visible dans la carte:")
        print(all_text)
        print("-"*60)
        
        # Chercher des éléments spécifiques
        elements_to_check = [
            ("h1", "Titre H1"),
            ("h2", "Titre H2"),
            ("h3", "Titre H3"),
            ("p", "Paragraphes"),
            ("span", "Spans"),
            ("div[class*='rating']", "Divs rating"),
            ("span[class*='rating']", "Spans rating"),
            ("div[class*='review']", "Divs review"),
            ("span[class*='review']", "Spans review"),
            ("div[class*='level']", "Divs level"),
            ("span[class*='level']", "Spans level"),
            ("div[class*='difficulty']", "Divs difficulty"),
            ("span[class*='star']", "Spans star"),
            ("svg", "SVG (icônes)"),
        ]
        
        print("\n📋 Éléments trouvés:")
        for selector, description in elements_to_check:
            try:
                elements = first_card.locator(selector)
                count = await elements.count()
                if count > 0:
                    print(f"\n   {description} ({selector}): {count} trouvé(s)")
                    for i in range(min(count, 3)):  # Max 3 exemples
                        try:
                            text = await elements.nth(i).inner_text(timeout=1000)
                            classes = await elements.nth(i).get_attribute("class")
                            print(f"      [{i}] Texte: {text[:80]}")
                            print(f"          Classes: {classes}")
                        except:
                            pass
            except:
                pass
        
        # Screenshot de la première carte
        print("\n📸 Capture d'écran de la première carte...")
        await first_card.screenshot(path="first_card.png")
        print("   Sauvegardée: first_card.png")
        
        print("\n" + "="*60)
        print("✅ Inspection terminée!")
        print("="*60)
        print("\nFichiers générés:")
        print("  - first_card.html (HTML complet)")
        print("  - first_card.png (Screenshot)")
        
        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_coursera())
