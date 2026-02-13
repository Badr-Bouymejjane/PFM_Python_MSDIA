"""
Système de Recommandation de Cours - Application Web Flask
Avec authentification utilisateur et recommandations personnalisées
"""

# === IMPORTATIONS DES BIBLIOTHÈQUES ===
import sys  # Module système pour accéder aux paramètres de l'interpréteur Python
import os  # Modules système pour l'accès aux fichiers et répertoires

import json  # Manipulation du format de données JSON (JavaScript Object Notation)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash  # Framework web Flask pour créer l'application
import pandas as pd  # Bibliothèque d'analyse de données (DataFrames) - manipulation de tableaux de données
from datetime import timedelta  # Gestion des durées temporelles (ex: durée de session)
from functools import wraps  # Outil pour créer des décorateurs (fonctions qui modifient d'autres fonctions)

# Importation des paramètres de configuration depuis le fichier config.py
from config import (
    FLASK_HOST,              # Adresse IP du serveur (ex: 0.0.0.0 ou localhost)
    FLASK_PORT,              # Port d'écoute du serveur web (ex: 2400)
    FLASK_DEBUG,             # Mode débogage activé/désactivé (True/False)
    SECRET_KEY,              # Clé secrète pour chiffrer les sessions utilisateur
    SESSION_LIFETIME_DAYS,   # Durée de validité de la session en jours
    CLEAN_DATA_PATH,         # Chemin vers le fichier CSV contenant les cours
    COURSES_PER_PAGE         # Nombre de cours affichés par page (pagination)
)
from models.recommender import CourseRecommender  # Moteur de recommandation (Logique métier) - algorithmes ML
from user_manager import UserManager  # Gestion des utilisateurs (Base de données SQLite)

# === CONFIGURATION DE L'APPLICATION FLASK ===
app = Flask(__name__)  # Initialisation de l'application Flask (création de l'instance)
app.secret_key = SECRET_KEY  # Clé secrète pour chiffrer les sessions (cookies sécurisés)
# Configuration de la durée de vie des sessions (combien de temps l'utilisateur reste connecté)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=SESSION_LIFETIME_DAYS)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Sécurité contre les attaques XSS (empêche JavaScript d'accéder aux cookies)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protection CSRF (Cross-Site Request Forgery)

# Fonctions globales accessibles dans les templates HTML (Jinja2)
# Permet d'utiliser max() et min() directement dans les fichiers HTML
app.jinja_env.globals.update(max=max, min=min)

# === INSTANCES GLOBALES (SINGLETONS) ===
# Un seul objet créé pour toute l'application (pattern Singleton)
recommender = CourseRecommender()  # Instance du moteur de recommandation (TF-IDF, Cosine Similarity)
user_manager = UserManager()  # Instance du gestionnaire d'utilisateurs (SQLite)


# === DÉCORATEUR DE PROTECTION DES ROUTES ===
def login_required(f):  # Décorateur personnalisé pour protéger l'accès aux pages
    """Vérifie si l'utilisateur est connecté avant d'accéder à une page"""
    @wraps(f)  # Préserve les métadonnées de la fonction originale (nom, docstring, etc.)
    def decorated_function(*args, **kwargs):
        # Vérifie si 'username' existe dans la session (cookie)
        if 'username' not in session:
            # Si non connecté, redirige vers la page de connexion
            return redirect(url_for('login'))
        # Si connecté, exécute la fonction protégée normalement
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Récupère le nom d'utilisateur depuis la session active"""
    # session.get() retourne None si la clé n'existe pas (évite les erreurs)
    return session.get('username')

# === INITIALISATION DU SYSTÈME DE RECOMMANDATION ===
def init_recommender():  # Initialisation et chargement du modèle de recommandation au démarrage
    """Charge ou entraîne le modèle de recommandation (TF-IDF + Cosine Similarity)"""
    global recommender  # Utilise la variable globale définie plus haut
    
    # Affichage du titre de l'application dans la console
    print("\n" + "="*60)
    print("   SYSTÈME DE RECOMMANDATION DE COURS")
    print("="*60 + "\n")
    
    # Vérifie si un modèle pré-entraîné existe déjà (fichier .pkl = pickle)
    if os.path.exists('models/recommender.pkl'):
        print("Chargement du modèle existant...")
        # Charger les données d'abord pour que load_model puisse vérifier la cohérence des colonnes
        recommender.load_data()  # Charge le CSV des cours
        if not recommender.load_model():  # Tente de charger le modèle sérialisé
            # Si le modèle pickle est incompatible avec les données actuelles, on ré-entraîne
            print("⚠️ Modèle obsolète ou incompatible. Ré-entraînement...")
            recommender.train()  # Entraîne le modèle TF-IDF sur les nouvelles données
            recommender.save_model()  # Sauvegarde le modèle pour les prochains démarrages
    else:
        # Aucun modèle existant : premier démarrage
        print("Entraînement du modèle...")
        recommender.train()  # Calcul de la matrice TF-IDF et de la similarité cosinus
        recommender.save_model()  # Sérialisation du modèle (pickle)
    
    # Vérification finale : le modèle est-il prêt ?
    if recommender.is_trained:
        stats = recommender.get_stats()  # Récupère les statistiques (nombre de cours, etc.)
        print(f"\nSystème prêt !")
        print(f"   {stats.get('total_courses', 0)} cours chargés")
        print(f"   Utilisateurs: {user_manager.get_all_users_count()}")
        return True  # Succès
    return False  # Échec

# === ROUTES D'AUTHENTIFICATION ===
# Les routes sont les URLs accessibles dans l'application web

@app.route('/login', methods=['GET', 'POST'])  # Accepte GET (affichage) et POST (soumission formulaire)
def login():  # Gestion de la connexion utilisateur
    """Page de connexion : affiche le formulaire et traite l'authentification"""
    # Vérifie si c'est une soumission de formulaire (POST) ou un simple affichage (GET)
    if request.method == 'POST':
        # Récupère les données du formulaire HTML
        username = request.form.get('username', '').strip()  # .strip() enlève les espaces
        password = request.form.get('password', '')  # Mot de passe brut (sera hashé)
        
        # Appelle la méthode de vérification dans le UserManager
        success, message = user_manager.login(username, password)  # Retourne (True/False, message)
        
        if success:  # Identifiants corrects
            session['username'] = username  # Crée une session (cookie chiffré)
            session.permanent = True  # La session persiste même après fermeture du navigateur
            return redirect(url_for('home'))  # Redirige vers la page d'accueil
        else:  # Identifiants incorrects
            return render_template('login.html', error=message)  # Affiche le message d'erreur
    
    # Si GET : affiche simplement le formulaire de connexion
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])  # Route pour l'inscription
def register():  # Gestion de l'inscription utilisateur
    """Page d'inscription : création d'un nouveau compte utilisateur"""
    if request.method == 'POST':  # Soumission du formulaire d'inscription
        # Récupération des champs du formulaire
        username = request.form.get('username', '').strip()  # Nom d'utilisateur
        email = request.form.get('email', '').strip()  # Adresse email
        password = request.form.get('password', '')  # Mot de passe
        confirm = request.form.get('confirm', '')  # Confirmation du mot de passe
        
        # === VALIDATION CÔTÉ SERVEUR ===
        # Vérification de la longueur minimale du nom d'utilisateur
        if len(username) < 3:
            return render_template('register.html', error="Username must be at least 3 characters")
        # Vérification de la longueur minimale du mot de passe
        if len(password) < 4:
            return render_template('register.html', error="Password must be at least 4 characters")
        # Vérification que les deux mots de passe correspondent
        if password != confirm:
            return render_template('register.html', error="Passwords do not match")
        
        # Appelle la méthode d'inscription dans le UserManager (hash du mot de passe + insertion BD)
        success, message = user_manager.register(username, email, password)
        
        if success:  # Inscription réussie
            session['username'] = username  # Connexion automatique après inscription
            session.permanent = True  # Session persistante
            return redirect(url_for('home'))  # Redirige vers l'accueil
        else:  # Échec (ex: nom d'utilisateur déjà pris)
            return render_template('register.html', error=message)
    
    # Si GET : affiche le formulaire d'inscription vide
    return render_template('register.html')

@app.route('/logout')  # Route de déconnexion
def logout():
    """Déconnecte l'utilisateur en supprimant sa session"""
    session.pop('username', None)  # Supprime 'username' de la session (déconnexion)
    return redirect(url_for('login'))  # Redirige vers la page de connexion

# === ROUTES WEB PRINCIPALES ===
# Ces routes affichent les pages HTML de l'application

@app.route('/')  # Route racine (page d'accueil)
@login_required  # Nécessite une connexion (décorateur)
def home():  # Page d'accueil : Tableau de bord principal
    """Tableau de bord personnalisé avec recommandations hybrides basées sur le comportement utilisateur"""
    # Récupération des informations de l'utilisateur connecté
    username = get_current_user()  # Nom d'utilisateur depuis la session
    user_prefs = user_manager.get_preferences(username)  # Récupération des préférences (catégories cliquées)
    user_stats = user_manager.get_user_stats(username)  # Statistiques (nombre de clics, recherches, etc.)
    
    # Récupération des métadonnées globales du système
    categories = recommender.get_categories()  # Liste de toutes les catégories disponibles
    platforms = recommender.get_platforms()  # Liste des plateformes (Coursera, Udemy, etc.)
    levels = recommender.get_levels()  # Niveaux de difficulté (Débutant, Intermédiaire, Avancé)
    stats = recommender.get_stats()  # Statistiques globales (nombre total de cours, etc.)
    
    # --- Moteur de Recommandation Hybride ---
    # Combine trois sources de recommandations :
    # 1. Historique de recherche (intentions explicites)
    # 2. Catégories préférées (comportement implicite au clic)
    # 3. Popularité globale (si pas assez de données)
    personalized_courses = []
    recommendation_reasons = {}
    
    # 1. Recommandations basées sur les recherches récentes
    # On regarde les derniers termes recherchés par l'utilisateur
    recent_searches = user_manager.get_recent_searches(username, 3)
    for query in recent_searches[:2]:
        if query:
            search_recs = recommender.recommend_by_query(query, n=3)
            for course in search_recs:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    recommendation_reasons[course['course_id']] = f"Basé sur votre recherche: '{query}'"
    
    # 2. Recommandations basées sur les catégories préférées (Proportionnel)
    # On analyse les clics précédents pour identifier les sujets d'intérêt
    cat_counts = user_prefs.get('categories', {})
    if cat_counts:
        # Prendre les 5 catégories les plus intéressantes
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        total_top_clicks = sum(count for cat, count in sorted_cats)
        
        # Nous voulons remplir environ 18-20 emplacements basés sur les intérêts de catégorie
        target_total_cat_recs = 20
        
        for cat, count in sorted_cats:
            # Calculer combien de cours montrer pour cette catégorie (poids proportionnel)
            # Plus l'utilisateur clique sur une catégorie, plus on lui en montre
            # Au moins 2 cours par sujet s'il est dans le top 5
            proportion = count / total_top_clicks
            n_to_fetch = max(2, round(proportion * target_total_cat_recs))
            
            # Obtenir les cours populaires dans cette catégorie
            cat_courses = recommender.get_popular_courses(n=n_to_fetch, category=cat)
            for course in cat_courses:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    # Ajouter la raison de la recommandation
                    recommendation_reasons[course['course_id']] = f"Car vous aimez: {cat}"
                    # Limiter le nombre de recommandations
                    if len(personalized_courses) >= 30: break
            if len(personalized_courses) >= 30: break
    else:
        # Repli pour les nouveaux utilisateurs sans clics
        top_cats = recommender.get_categories()[:3]
        for cat in top_cats:
            cat_courses = recommender.get_popular_courses(n=4, category=cat)
            for course in cat_courses:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    recommendation_reasons[course['course_id']] = f"Découvrez: {cat}"
    
    
    # 3. Remplir avec des cours populaires si nécessaire
    if len(personalized_courses) < 15:
        popular = recommender.get_popular_courses(n=25)
        for course in popular:
            if len(personalized_courses) >= 25:
                break
            if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                personalized_courses.append(course)
                recommendation_reasons[course['course_id']] = "Cours populaire"
    
    # Ajouter des raisons explicatives et calculer des scores de similarité
    import random
    total_clicks = sum(cat_counts.values()) or 1
    
    for course in personalized_courses:
        # Raison affichée sur la carte du cours (ex: "Basé sur votre recherche python")
        course['reason'] = recommendation_reasons.get(course['course_id'], '')
        
        # Si le score existe déjà (venant du moteur de recherche), on l'ajuste
        # Sinon on le calcule basé sur les métadonnées
        
        current_score = course.get('similarity_score')
        
        if current_score:
            # C'est un résultat de recherche directe ou recommandation ML
            # On normalise si c'est > 1 (le moteur retourne 0-100)
            if current_score <= 1: current_score *= 100
                
            # DIVERSIFICATION : Réduire légèrement le score si on a déjà fait d'autres actions
            # Si l'utilisateur a beaucoup d'autres intérêts, une seule recherche pèse moins lourd
            if total_clicks > 5:
                penalty = min(total_clicks * 0.5, 15.0) # Jusqu'à 15% de pénalité si très actif ailleurs
                current_score -= penalty
        else:
            # Calcul heuristique pour les recommandations par catégorie/popularité
            if 'recherche' in course['reason'].lower():
                base = 85.0
            elif 'aimez' in course['reason'].lower():
                # Poids dynamique basé sur l'intérêt pour cette catégorie spécifique
                cat_name = course.get('category')
                cat_interest = cat_counts.get(cat_name, 0)
                
                # Ratio d'intérêt : part de cette catégorie dans l'historique total (0.0 à 1.0)
                interest_ratio = cat_interest / total_clicks
                
                # Le score reflète la part d'intérêt : 
                # Si 100% des clics sont ici -> ~95%
                # Si 10% des clics sont ici -> ~75%
                base = 70.0 + (interest_ratio * 25.0) 
            elif 'populaire' in course['reason'].lower():
                base = 60.0
            else:
                base = 50.0
            
            # Ajouter un bonus de qualité du cours (Note)
            rating = course.get('rating', 0)
            quality_bonus = max(0, (rating - 4.0) * 10) # +0 à +10 points pour 4.0 à 5.0
            
            current_score = base + quality_bonus
            
        # Ajout de bruit aléatoire pour éviter les scores trop ronds
        final_score = current_score + random.uniform(-2.0, 2.0)
        
        # Bornage du score (Note finale de pertinence entre 40 et 99)
        course['similarity_score'] = round(max(40.0, min(99.0, final_score)), 1)
    
    # Trier les recommandations par le score calculé pour que les sujets favoris apparaissent en premier
    personalized_courses.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    return render_template('home.html',
                         username=username,
                         user_stats=user_stats,
                         user_prefs=user_prefs,
                         categories=categories,
                         platforms=platforms,
                         levels=levels,
                         stats=stats,
                         personalized_courses=personalized_courses[:20],
                         recent_searches=recent_searches)

@app.route('/courses')  # Route pour le catalogue complet
@login_required  # Nécessite une connexion
def courses():  # Catalogue des cours : Recherche, Filtrage et Pagination
    """Page de catalogue avec recherche, filtres (catégorie, plateforme, niveau) et tri intelligent"""
    username = get_current_user()  # Utilisateur connecté
    
    # === RÉCUPÉRATION DES PARAMÈTRES DE L'URL (Query Parameters) ===
    page = request.args.get('page', 1, type=int)  # Numéro de page (pagination)
    sort_by = request.args.get('sort', 'recommendation')  # Méthode de tri (recommendation, rating, popularity)
    platform = request.args.get('platform', '')  # Filtre par plateforme (ex: Coursera)
    category = request.args.get('category', '')  # Filtre par catégorie (ex: Data Science)
    level = request.args.get('level', '')  # Filtre par niveau (ex: Beginner)
    search = request.args.get('search', '')  # Terme de recherche textuelle
    
    # Construction du dictionnaire de filtres pour le moteur de recommandation
    filters = {}  # Dictionnaire vide au départ
    if platform: filters['platform'] = platform  # Ajoute le filtre seulement s'il est défini
    if category: filters['category'] = category
    if level: filters['level'] = level
    if search: filters['search'] = search
        
    if sort_by == 'recommendation':
        # Mode Recommandation Intelligente
        # 1. On récupère d'abord tous les candidats possibles (filtrés par catégories/niveau etc)
        # Obtenir tous les cours en passant une grande valeur per_page ou en calculant le total
        total_count = len(recommender.df) if recommender.df is not None else 1000
        all_filtered = recommender.get_all_courses(page=1, per_page=total_count, sort_by='rating', filters=filters)['courses']
        
        # Le but est de re-trier cette liste `all_filtered` selon la pertinence utilisateur
        
        # 1. Essayer les recommandations basées sur l'historique de recherche
        recent_searches = user_manager.get_recent_searches(username, n=3)
        
        # 2. Essayer les recommandations basées sur les catégories principales (d'après les clics)
        top_cats = user_manager.get_top_categories(username, n=2)
        
        query_text = ""
        if recent_searches:
            # On donne un poids normal aux recherches
            query_text += " ".join(recent_searches)
        if top_cats:
            # On BOOSTE les catégories (x3) pour compenser leur IDF souvent plus faible
            # (IDF = Inverse Document Frequency : un mot commun pèse moins lourd)
            # Cela permet aux interactions récentes (clics) d'avoir plus d'impact face aux recherches textuelles
            cat_text = " ".join(top_cats)
            query_text += " " + (cat_text + " ") * 3
            
        if query_text.strip():
            # Recommandation personnalisée via TF-IDF / Cosine Similarity
            # On demande au moteur de trouver les cours proches du "profil textuel" construit ci-dessus
            recs = recommender.recommend_by_query(query_text, n=len(all_filtered), filters=filters)
            rec_map = {r['course_id']: r['similarity_score'] for r in recs}
            
            # Importer les modules nécessaires
            import math
            import random
            
            # Trouver le score max pour la normalisation
            # On s'assure que le max n'est pas trop bas pour éviter de booster du bruit
            max_sim = max(rec_map.values()) if rec_map else 1.0
            max_sim = max(max_sim, 0.1) # Seuil minimal
            
            for c in all_filtered:
                raw_sim = rec_map.get(c['course_id'], 0)
                
                # Validation : Si le score brut est trop faible (< 0.05), on le considère comme nul
                # sauf si c'est une correspondance exacte (rare)
                if raw_sim < 0.01:
                    raw_sim = 0
                
                # Boost et Mise à l'échelle
                if raw_sim > 0:
                    normalized = raw_sim / max_sim
                    
                    # Formule adoucie :
                    # On veut que même les items avec une similarité moyenne (0.3-0.5) aient un score décent (60-70%)
                    # Score = Base 50 + (sqrt(Normalisé) * 45) + (Bonus Note)
                    # La racine carrée remonte les scores moyens vers le haut
                    rating_bonus = (c.get('rating', 0) - 3.0) * 3 if c.get('rating', 0) > 3.0 else 0
                    scaled_score = 50 + (math.sqrt(normalized) * 40) + rating_bonus
                    
                    # Ajouter un petit facteur aléatoire
                    scaled_score += random.uniform(-1.5, 1.5)
                    
                    c['similarity_score'] = round(max(40.0, min(99.5, scaled_score)), 1)
                else:
                    c['similarity_score'] = 0
                    
            # Tri final par score décroissant
            all_filtered.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        else:
            # Repli : Mélanger aléatoirement si pas d'historique utilisateur pour éviter une liste statique
            # C'est important pour la découverte ("Serendipity")
            import random
            random.shuffle(all_filtered)
        
        total = len(all_filtered)
        start = (page - 1) * COURSES_PER_PAGE
        end = start + COURSES_PER_PAGE
        courses_list = all_filtered[start:end]
        pages = (total + COURSES_PER_PAGE - 1) // COURSES_PER_PAGE
        result = {'courses': courses_list, 'total': total, 'pages': pages, 'current_page': page}
    else:
        result = recommender.get_all_courses(page=page, per_page=COURSES_PER_PAGE, sort_by=sort_by, filters=filters)
    
    # Suivre la recherche si elle renvoie des résultats
    if search and result['total'] > 0:
        user_manager.track_search(username, search)
    
    return render_template('courses.html',
                         username=username,
                         courses=result['courses'],
                         total=result['total'],
                         pages=result['pages'],
                         current_page=result.get('current_page', page),
                         categories=recommender.get_categories(),
                         platforms=recommender.get_platforms(),
                         levels=recommender.get_levels(),
                         current_filters={'platform': platform, 'category': category, 'level': level, 'search': search, 'sort': sort_by})

@app.route('/course/<int:course_id>')  # Route dynamique avec paramètre (ID du cours)
@login_required  # Nécessite une connexion
def course_detail(course_id):  # Page de détail d'un cours spécifique
    """Affiche les détails complets d'un cours + recommandations de cours similaires"""
    username = get_current_user()  # Utilisateur connecté
    course = recommender.get_course_by_id(course_id)  # Récupère les détails du cours depuis le DataFrame
    
    # Vérification : le cours existe-t-il ?
    if not course:
        return redirect(url_for('courses'))  # Redirige vers le catalogue si cours introuvable
    
    # === TRACKING DU COMPORTEMENT UTILISATEUR ===
    # Enregistre que l'utilisateur a consulté ce cours (pour les statistiques)
    user_manager.track_view(username, course_id)
    # Enregistre le clic (pour construire le profil d'intérêts)
    user_manager.track_click(username, course)
    
    # Recommandation "Item-based" : Cours similaires à celui-ci (Collaborative Filtering)
    # Utilise la similarité cosinus pour trouver des cours proches
    similar_courses = recommender.recommend_similar(course_id, n=6)  # Top 6 cours similaires
    
    # Rendu du template HTML avec les données
    return render_template('course_detail.html',
                         username=username,
                         course=course,
                         similar_courses=similar_courses)

@app.route('/profile')  # Route pour le profil utilisateur
@login_required  # Nécessite une connexion
def profile():
    """Page de profil : affiche les statistiques, préférences et parcours sauvegardés de l'utilisateur"""
    username = get_current_user()  # Utilisateur connecté
    user = user_manager.get_user(username)  # Récupère les infos utilisateur (email, date d'inscription, etc.)
    
    # Vérification de sécurité : l'utilisateur existe-t-il dans la base de données ?
    if not user:
        # Si la session existe mais l'utilisateur n'est pas dans la BD (après migration ou suppression)
        flash("Utilisateur introuvable. Veuillez vous reconnecter.")  # Message flash (notification)
        return redirect(url_for('logout'))  # Force la déconnexion
    
    # Récupération des données du profil
    stats = user_manager.get_user_stats(username)  # Statistiques d'activité (clics, recherches, etc.)
    prefs = user_manager.get_preferences(username)  # Préférences (catégories favorites)
    saved_paths = user_manager.get_saved_paths(username)  # Parcours d'apprentissage sauvegardés
    
    # Rendu du template avec toutes les données du profil
    return render_template('profile.html',
                         username=username,
                         user=user,
                         stats=stats,
                         preferences=prefs,
                         saved_paths=saved_paths)

@app.route('/report')  # Route pour la page de rapport
@login_required  # Nécessite une connexion
def report():
    """Page de rapport : affiche des analyses et visualisations du système"""
    return render_template('report.html', username=get_current_user())

# === ROUTES API (Pour les interactions AJAX/JavaScript) ===
# Ces routes retournent des données JSON (pas de HTML) pour les requêtes asynchrones

@app.route('/api/search', methods=['POST'])  # Accepte uniquement les requêtes POST
@login_required  # Nécessite une connexion
def api_search():
    """API de recherche instantanée : retourne des recommandations basées sur une requête textuelle (AJAX)"""
    username = get_current_user()  # Utilisateur connecté
    data = request.get_json()  # Récupère les données JSON envoyées par le client (JavaScript)
    query = data.get('query', '')  # Terme de recherche
    n = data.get('n', 20)  # Nombre de résultats souhaités (par défaut 20)
    
    # Requête AJAX pour la barre de recherche instantanée (auto-complétion)
    if not query:  # Validation : la requête est-elle vide ?
        return jsonify({'error': 'Query required'}), 400  # Erreur HTTP 400 (Bad Request)
    
    # Appel du moteur de recommandation (TF-IDF + Cosine Similarity)
    recommendations = recommender.recommend_by_query(query, n)
    
    # Suivre la recherche uniquement si des résultats sont trouvés et pertinents
    # Nous vérifions si nous avons des résultats et si le meilleur résultat a au moins une certaine similarité (ex. 15%)
    if recommendations and recommendations[0].get('similarity_score', 0) > 15:
        user_manager.track_search(username, query)  # Enregistre la recherche dans la BD
    else:
        print(f"🔍 Recherche pour '{query}' ignorée (pas de résultats pertinents trouvés)")
    
    # Retourne les résultats au format JSON
    return jsonify({
        'recommendations': recommendations,  # Liste des cours recommandés
        'query': query,  # Requête originale
        'count': len(recommendations)  # Nombre de résultats
    })

@app.route('/api/recommend/<int:course_id>')  # Route API avec paramètre dynamique
@login_required  # Nécessite une connexion
def api_recommend(course_id):
    """API de recommandation item-based : retourne des cours similaires à un cours donné"""
    n = request.args.get('n', 6, type=int)
    similar = recommender.recommend_similar(course_id, n)
    return jsonify({'course_id': course_id, 'recommendations': similar, 'count': len(similar)})

@app.route('/api/courses')  # API pour récupérer la liste des cours
@login_required  # Nécessite une connexion
def api_courses():
    """API de catalogue : retourne une liste paginée et filtrée de cours (JSON)"""
    # Récupération des paramètres de pagination et tri depuis l'URL
    page = request.args.get('page', 1, type=int)  # Numéro de page
    per_page = request.args.get('per_page', 20, type=int)  # Cours par page
    sort_by = request.args.get('sort', 'rating')  # Méthode de tri (rating, popularity, etc.)
    
    # Construction dynamique des filtres à partir des paramètres URL
    filters = {}  # Dictionnaire vide au départ
    for key in ['platform', 'category', 'level', 'search', 'min_rating']:  # Liste des filtres possibles
        if request.args.get(key):  # Si le paramètre existe dans l'URL
            filters[key] = request.args.get(key)  # Ajoute au dictionnaire
    
    # Appel du moteur de recommandation avec les paramètres
    result = recommender.get_all_courses(page, per_page, sort_by, filters)
    return jsonify(result)  # Retourne le résultat au format JSON

@app.route('/api/track/click', methods=['POST'])  # Tracking des clics (POST uniquement)
@login_required  # Nécessite une connexion
def api_track_click():
    """API de tracking : enregistre un clic utilisateur sur un cours (pour le profil d'intérêts)"""
    username = get_current_user()
    data = request.get_json()
    course_id = data.get('course_id')
    
    if course_id is not None:
        course = recommender.get_course_by_id(course_id)
        if course:
            user_manager.track_click(username, course)
    
    return jsonify({'status': 'ok'})

@app.route('/api/user/stats')  # API pour les statistiques utilisateur
@login_required  # Nécessite une connexion
def api_user_stats():
    """API de statistiques : retourne les stats d'activité de l'utilisateur (clics, recherches, etc.)"""
    username = get_current_user()
    stats = user_manager.get_user_stats(username)
    return jsonify(stats)

@app.route('/api/stats')  # API pour les statistiques globales (pas de login requis)
def api_stats():
    """API de statistiques globales : retourne les stats du système (nombre de cours, catégories, etc.)"""
    return jsonify(recommender.get_stats())

@app.route('/api/popular')  # API pour les cours populaires (pas de login requis)
def api_popular():
    """API de popularité : retourne les cours les plus populaires (tri par nombre de vues/notes)"""
    n = request.args.get('n', 10, type=int)
    category = request.args.get('category', None)
    popular = recommender.get_popular_courses(n, category)
    return jsonify({'courses': popular, 'count': len(popular)})

# === ROUTES DE CLUSTERING (Analyse et Visualisation) ===
# Le clustering regroupe les cours similaires en clusters (groupes) via K-Means

clustering_instance = None  # Variable globale pour stocker l'instance de clustering

def get_clustering():  # Instance unique du modèle de clustering (Lazy Loading)
    """Charge ou crée l'instance de clustering (pattern Singleton avec initialisation paresseuse)"""
    global clustering_instance  # Utilise la variable globale
    if clustering_instance is None:  # Si pas encore initialisé
        from models.clustering import CourseClustering  # Import local (pour éviter les imports circulaires)
        clustering_instance = CourseClustering(n_clusters=24)  # Crée une instance avec 24 clusters
        clustering_instance.run()  # Lance l'algorithme K-Means (TF-IDF + clustering)
    return clustering_instance  # Retourne l'instance (existante ou nouvellement créée)

@app.route('/clustering')  # Route pour la page de visualisation des clusters
@login_required  # Nécessite une connexion
def clustering():  # Page de visualisation des clusters (Groupes de cours similaires)
    """Page interactive de visualisation des clusters (graphique 2D avec PCA/t-SNE)"""
    # Récupère le modèle de clustering (K-Means) pour visualiser les regroupements de cours
    clustering_model = get_clustering()  # Charge ou crée l'instance
    viz_data = clustering_model.get_visualization_data()  # Coordonnées PCA/t-SNE pour le graphique 2D
    clusters_info = clustering_model.get_cluster_info()  # Informations sur chaque cluster (taille, catégories, etc.)
    categories = recommender.get_categories()  # Liste des catégories disponibles
    
    # Palette de couleurs étendue pour couvrir tous les clusters potentiels (24 couleurs)
    # Chaque cluster aura une couleur distincte dans la visualisation
    cluster_colors = [
        '#4f46e5', '#10b981', '#f59e0b', '#ef4444',  # Bleu, Vert, Orange, Rouge
        '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16',  # Violet, Cyan, Rose, Lime
        '#22c55e', '#3b82f6', '#6366f1', '#a855f7',  # Vert clair, Bleu clair, Indigo, Violet clair
        '#d946ef', '#f43f5e', '#f97316', '#eab308'   # Magenta, Rose foncé, Orange foncé, Jaune
    ]
    
    # Rendu du template avec toutes les données de clustering
    return render_template('clustering.html',
                         username=get_current_user(),
                         viz_data=json.dumps(viz_data),  # Conversion en JSON pour JavaScript
                         clusters_info=clusters_info,
                         cluster_colors=cluster_colors,
                         categories=categories,
                         total_courses=len(clustering_model.df),  # Nombre total de cours
                         n_clusters=len(clusters_info),  # Nombre de clusters
                         n_categories=len(categories))  # Nombre de catégories

@app.route('/dashboard')  # Route pour le tableau de bord analytique
@login_required  # Nécessite une connexion
def dashboard():
    """Tableau de bord analytique : graphiques et statistiques sur les cours et clusters (Chart.js)"""
    username = get_current_user()  # Utilisateur connecté
    clustering_model = get_clustering()  # Récupère le modèle de clustering
    
    # === PRÉPARATION DES DONNÉES POUR LES GRAPHIQUES (Chart.js) ===
    
    # 1. Cours par Catégorie (Top 10) - Graphique en barres
    # value_counts() compte le nombre d'occurrences de chaque catégorie
    cat_counts = recommender.df['category'].value_counts().head(10).to_dict()
    
    # 2. Préparer les Données du Graphique - Cours par Plateforme (Diagramme circulaire)
    platform_counts = recommender.df['platform'].value_counts().to_dict()
    
    # 3. Préparer les Données du Graphique - Distribution des Clusters (Histogramme)
    # Compte le nombre de cours dans chaque cluster (0, 1, 2, ..., 23)
    cluster_counts = clustering_model.df['cluster'].value_counts().sort_index().tolist()
    cluster_labels = [f"Cluster {i}" for i in range(len(cluster_counts))]  # Labels pour l'axe X
    
    # 4. Préparer les Données du Graphique - Note Moyenne par Plateforme (Graphique en barres)
    # groupby() regroupe par plateforme, mean() calcule la moyenne
    avg_ratings = recommender.df.groupby('platform')['rating'].mean().to_dict()
    
    # 5. Stats Résumées (Cartes de statistiques)
    stats = recommender.get_stats()  # Nombre total de cours, catégories, etc.
    
    # Rendu du template avec toutes les données pour les graphiques
    return render_template('dashboard.html',
                         username=username,
                         cat_data=json.dumps(cat_counts),  # Conversion en JSON pour JavaScript
                         platform_data=json.dumps(platform_counts),
                         cluster_data=json.dumps(cluster_counts),
                         cluster_labels=json.dumps(cluster_labels),
                         rating_data=json.dumps(avg_ratings),
                         stats=stats)

@app.route('/api/learning-path')  # API pour générer un parcours d'apprentissage
@login_required  # Nécessite une connexion
def api_learning_path():
    """API de parcours d'apprentissage : génère une séquence de cours (Débutant → Avancé) pour une catégorie"""
    category = request.args.get('category', '')  # Catégorie demandée (ex: "Data Science")
    if not category:  # Validation : la catégorie est-elle fournie ?
        return jsonify({'error': 'Category required', 'path': []})  # Erreur si manquante
    
    # Génère un parcours d'apprentissage séquentiel basé sur le clustering
    # Suggère une suite logique de cours (Débutant → Intermédiaire → Avancé)
    clustering_model = get_clustering()  # Récupère le modèle de clustering
    path = clustering_model.get_learning_path(category)  # Génère le parcours
    return jsonify({'category': category, 'path': path})  # Retourne le parcours au format JSON

@app.route('/api/clusters')  # API pour récupérer les données de clustering (pas de login requis)
def api_clusters():
    """API de clustering : retourne les données de visualisation des clusters (coordonnées 2D)"""
    clustering_model = get_clustering()
    return jsonify(clustering_model.get_visualization_data())

@app.route('/api/save-path', methods=['POST'])  # API pour sauvegarder un parcours (POST uniquement)
@login_required  # Nécessite une connexion
def api_save_path():
    """API de sauvegarde : enregistre un parcours d'apprentissage personnalisé pour l'utilisateur"""
    username = get_current_user()
    data = request.get_json()
    category = data.get('category')
    path_data = data.get('path')
    
    if not category or not path_data:
        return jsonify({'error': 'Missing data'}), 400
        
    user_manager.save_path(username, category, path_data)
    return jsonify({'status': 'ok'})

# === POINT D'ENTRÉE PRINCIPAL (MAIN) ===
# Ce bloc s'exécute uniquement si le script est lancé directement (pas importé)
if __name__ == '__main__':  # Vérifie si c'est le fichier principal
    # Initialise le système de recommandation (charge ou entraîne le modèle)
    if init_recommender():  # Si l'initialisation réussit
        print(f"\nDémarrage du serveur Flask...")  # Message de confirmation
        print(f"Accédez à : http://localhost:2400\n")  # URL d'accès
        # Lance le serveur web Flask avec les paramètres de configuration
        app.run(
            debug=FLASK_DEBUG,  # Mode débogage (rechargement automatique, messages d'erreur détaillés)
            host=FLASK_HOST,    # Adresse IP (0.0.0.0 = accessible depuis le réseau, 127.0.0.1 = local uniquement)
            port=FLASK_PORT     # Port d'écoute (2400)
        )
    else:  # Si l'initialisation échoue
        print("\nImpossible de démarrer l'application")  # Message d'erreur
