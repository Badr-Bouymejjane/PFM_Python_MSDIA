"""
Système de Recommandation de Cours - Application Web Flask
Avec authentification utilisateur et recommandations personnalisées
"""

import sys
import os

import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
from datetime import timedelta
from functools import wraps

from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    SECRET_KEY, SESSION_LIFETIME_DAYS,
    CLEAN_DATA_PATH, COURSES_PER_PAGE
)
from models.recommender import CourseRecommender
from user_manager import UserManager

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=SESSION_LIFETIME_DAYS)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Fonctions globales pour les modèles Jinja
app.jinja_env.globals.update(max=max, min=min)

recommender = CourseRecommender()
user_manager = UserManager()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    return session.get('username')

def init_recommender():
    global recommender
    
    print("\n" + "="*60)
    print("   SYSTÈME DE RECOMMANDATION DE COURS")
    print("="*60 + "\n")
    
    if os.path.exists('models/recommender.pkl'):
        print("Chargement du modèle existant...")
        # Charger les données d'abord pour que load_model puisse vérifier la cohérence
        recommender.load_data()
        if not recommender.load_model():
            print("⚠️ Modèle obsolète ou incompatible. Ré-entraînement...")
            recommender.train()
            recommender.save_model()
    else:
        print("Entraînement du modèle...")
        recommender.train()
        recommender.save_model()
        
    if recommender.is_trained:
        stats = recommender.get_stats()
        print(f"\nSystème prêt !")
        print(f"   {stats.get('total_courses', 0)} cours chargés")
        print(f"   Utilisateurs: {user_manager.get_all_users_count()}")
        return True
    return False

# ROUTES D'AUTHENTIFICATION
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message = user_manager.login(username, password)
        
        if success:
            session['username'] = username
            session.permanent = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error=message)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        
        if len(username) < 3:
            return render_template('register.html', error="Username must be at least 3 characters")
        if len(password) < 4:
            return render_template('register.html', error="Password must be at least 4 characters")
        if password != confirm:
            return render_template('register.html', error="Passwords do not match")
            
        success, message = user_manager.register(username, email, password)
        
        if success:
            session['username'] = username
            session.permanent = True
            return redirect(url_for('home'))
        else:
            return render_template('register.html', error=message)
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# ROUTES WEB
@app.route('/')
@login_required
def home():
    username = get_current_user()
    user_prefs = user_manager.get_preferences(username)
    user_stats = user_manager.get_user_stats(username)
    
    categories = recommender.get_categories()
    platforms = recommender.get_platforms()
    levels = recommender.get_levels()
    stats = recommender.get_stats()
    
    # Construire des recommandations personnalisées
    personalized_courses = []
    recommendation_reasons = {}
    
    # 1. Recommandations basées sur les recherches récentes
    recent_searches = user_manager.get_recent_searches(username, 3)
    for query in recent_searches[:2]:
        if query:
            search_recs = recommender.recommend_by_query(query, n=3)
            for course in search_recs:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    recommendation_reasons[course['course_id']] = f"Basé sur votre recherche: '{query}'"
    
    # 2. Recommandations basées sur les catégories préférées (Proportionnel)
    cat_counts = user_prefs.get('categories', {})
    if cat_counts:
        # Prendre les 5 catégories les plus intéressantes
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        total_top_clicks = sum(count for cat, count in sorted_cats)
        
        # Nous voulons remplir environ 18-20 emplacements basés sur les intérêts de catégorie
        target_total_cat_recs = 20
        
        for cat, count in sorted_cats:
            # Calculer combien de cours montrer pour cette catégorie (poids proportionnel)
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
    
    # Ajouter des raisons et des scores de similarité aux cours
    import random
    total_clicks = sum(cat_counts.values()) or 1
    
    for course in personalized_courses:
        course['reason'] = recommendation_reasons.get(course['course_id'], '')
        
        # Si le score existe déjà (venant du moteur de recherche), on l'ajuste
        # Sinon on le calcule basé sur les métadonnées
        
        current_score = course.get('similarity_score')
        
        if current_score:
            # C'est un résultat de recherche directe ou recommandation ML
            # On normalise si c'est > 1 (le moteur retourne 0-100)
            if current_score <= 1: current_score *= 100
                
            # DIVERSIFICATION : Réduire légèrement le score si on a déjà fait d'autres actions
            # Si l'utilisateur a beaucoup d'autres intérêts, la recherche unique a moins de poids absolu
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
        
        # Bornage du score (40% - 99%)
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

@app.route('/courses')
@login_required
def courses():
    username = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'recommendation')  # Par défaut : recommandation
    platform = request.args.get('platform', '')
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    
    filters = {}
    if platform: filters['platform'] = platform
    if category: filters['category'] = category
    if level: filters['level'] = level
    if search: filters['search'] = search
        
    if sort_by == 'recommendation':
        # Obtenir tous les cours en passant une grande valeur per_page ou en calculant le total
        total_count = len(recommender.df) if recommender.df is not None else 1000
        all_filtered = recommender.get_all_courses(page=1, per_page=total_count, sort_by='rating', filters=filters)['courses']
        
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
            # Cela permet aux interactions récentes (clics) d'avoir plus d'impact face aux recherches
            cat_text = " ".join(top_cats)
            query_text += " " + (cat_text + " ") * 3
            
        if query_text.strip():
            # Recommandation personnalisée
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
                    
            all_filtered.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        else:
            # Repli : Mélanger si pas d'historique utilisateur pour éviter une liste générique statique
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

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    username = get_current_user()
    course = recommender.get_course_by_id(course_id)
    
    if not course:
        return redirect(url_for('courses'))
    
    # Suivre la vue
    user_manager.track_view(username, course_id)
    user_manager.track_click(username, course)
    
    similar_courses = recommender.recommend_similar(course_id, n=6)
    return render_template('course_detail.html',
                         username=username,
                         course=course,
                         similar_courses=similar_courses)

@app.route('/profile')
@login_required
def profile():
    username = get_current_user()
    user = user_manager.get_user(username)
    
    if not user:
        # Si la session existe mais l'utilisateur n'est pas dans la BD (après migration ou suppression)
        flash("Utilisateur introuvable. Veuillez vous reconnecter.")
        return redirect(url_for('logout'))
        
    stats = user_manager.get_user_stats(username)
    prefs = user_manager.get_preferences(username)
    saved_paths = user_manager.get_saved_paths(username)
    
    return render_template('profile.html',
                         username=username,
                         user=user,
                         stats=stats,
                         preferences=prefs,
                         saved_paths=saved_paths)

@app.route('/report')
@login_required
def report():
    return render_template('report.html', username=get_current_user())

# ROUTES API
@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    username = get_current_user()
    data = request.get_json()
    query = data.get('query', '')
    n = data.get('n', 20)
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    recommendations = recommender.recommend_by_query(query, n)
    
    # Suivre la recherche uniquement si des résultats sont trouvés et pertinents
    # Nous vérifions si nous avons des résultats et si le meilleur résultat a au moins une certaine similarité (ex. 15%)
    if recommendations and recommendations[0].get('similarity_score', 0) > 15:
        user_manager.track_search(username, query)
    else:
        print(f"🔍 Recherche pour '{query}' ignorée (pas de résultats pertinents trouvés)")
    
    return jsonify({
        'recommendations': recommendations,
        'query': query,
        'count': len(recommendations)
    })

@app.route('/api/recommend/<int:course_id>')
@login_required
def api_recommend(course_id):
    n = request.args.get('n', 6, type=int)
    similar = recommender.recommend_similar(course_id, n)
    return jsonify({'course_id': course_id, 'recommendations': similar, 'count': len(similar)})

@app.route('/api/courses')
@login_required
def api_courses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort', 'rating')
    
    filters = {}
    for key in ['platform', 'category', 'level', 'search', 'min_rating']:
        if request.args.get(key):
            filters[key] = request.args.get(key)
            
    result = recommender.get_all_courses(page, per_page, sort_by, filters)
    return jsonify(result)

@app.route('/api/track/click', methods=['POST'])
@login_required
def api_track_click():
    username = get_current_user()
    data = request.get_json()
    course_id = data.get('course_id')
    
    if course_id is not None:
        course = recommender.get_course_by_id(course_id)
        if course:
            user_manager.track_click(username, course)
    
    return jsonify({'status': 'ok'})

@app.route('/api/user/stats')
@login_required
def api_user_stats():
    username = get_current_user()
    stats = user_manager.get_user_stats(username)
    return jsonify(stats)

@app.route('/api/stats')
def api_stats():
    return jsonify(recommender.get_stats())

@app.route('/api/popular')
def api_popular():
    n = request.args.get('n', 10, type=int)
    category = request.args.get('category', None)
    popular = recommender.get_popular_courses(n, category)
    return jsonify({'courses': popular, 'count': len(popular)})

# ROUTES DE CLUSTERING
clustering_instance = None

def get_clustering():
    global clustering_instance
    if clustering_instance is None:
        from models.clustering import CourseClustering
        clustering_instance = CourseClustering(n_clusters=24)
        clustering_instance.run()
    return clustering_instance

@app.route('/clustering')
@login_required
def clustering():
    clustering_model = get_clustering()
    viz_data = clustering_model.get_visualization_data()
    clusters_info = clustering_model.get_cluster_info()
    categories = recommender.get_categories()
    
    # Palette de couleurs étendue pour couvrir tous les clusters potentiels
    cluster_colors = [
        '#4f46e5', '#10b981', '#f59e0b', '#ef4444', 
        '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16',
        '#22c55e', '#3b82f6', '#6366f1', '#a855f7',
        '#d946ef', '#f43f5e', '#f97316', '#eab308'
    ]
    
    return render_template('clustering.html',
                         username=get_current_user(),
                         viz_data=json.dumps(viz_data),
                         clusters_info=clusters_info,
                         cluster_colors=cluster_colors,
                         categories=categories,
                         total_courses=len(clustering_model.df),
                         n_clusters=len(clusters_info),
                         n_categories=len(categories))

@app.route('/dashboard')
@login_required
def dashboard():
    username = get_current_user()
    clustering_model = get_clustering()
    
    # 1. Préparer les Données du Graphique - Cours par Catégorie
    cat_counts = recommender.df['category'].value_counts().head(10).to_dict()
    
    # 2. Préparer les Données du Graphique - Cours par Plateforme
    platform_counts = recommender.df['platform'].value_counts().to_dict()
    
    # 3. Préparer les Données du Graphique - Distribution des Clusters (via le modèle de clustering)
    cluster_counts = clustering_model.df['cluster'].value_counts().sort_index().tolist()
    cluster_labels = [f"Cluster {i}" for i in range(len(cluster_counts))]
    
    # 4. Préparer les Données du Graphique - Note Moyenne par Plateforme
    avg_ratings = recommender.df.groupby('platform')['rating'].mean().to_dict()
    
    # 5. Stats Résumées
    stats = recommender.get_stats()
    
    return render_template('dashboard.html',
                         username=username,
                         cat_data=json.dumps(cat_counts),
                         platform_data=json.dumps(platform_counts),
                         cluster_data=json.dumps(cluster_counts),
                         cluster_labels=json.dumps(cluster_labels),
                         rating_data=json.dumps(avg_ratings),
                         stats=stats)

@app.route('/api/learning-path')
@login_required
def api_learning_path():
    category = request.args.get('category', '')
    if not category:
        return jsonify({'error': 'Category required', 'path': []})
    
    clustering_model = get_clustering()
    path = clustering_model.get_learning_path(category)
    return jsonify({'category': category, 'path': path})

@app.route('/api/clusters')
def api_clusters():
    clustering_model = get_clustering()
    return jsonify(clustering_model.get_visualization_data())

@app.route('/api/save-path', methods=['POST'])
@login_required
def api_save_path():
    username = get_current_user()
    data = request.get_json()
    category = data.get('category')
    path_data = data.get('path')
    
    if not category or not path_data:
        return jsonify({'error': 'Missing data'}), 400
        
    user_manager.save_path(username, category, path_data)
    return jsonify({'status': 'ok'})

# MAIN
if __name__ == '__main__':
    if init_recommender():
        print(f"\nDémarrage du serveur Flask...")
        print(f"Accédez à : http://localhost:2400\n")
        app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
    else:
        print("\nImpossible de démarrer l'application")
