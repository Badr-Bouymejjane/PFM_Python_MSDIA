"""
Application Web Flask - Système de Recommandation de Cours
Version simplifiée et claire
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
from functools import wraps
import os

# Import des modules personnalisés
from database import Database
from recommender_simple import RecommendationSystem

# =====================================
# CONFIGURATION DE L'APPLICATION
# =====================================

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# =====================================
# INITIALISATION DES COMPOSANTS
# =====================================

db = Database()
recommender = RecommendationSystem()

# =====================================
# DÉCORATEUR POUR PROTÉGER LES ROUTES
# =====================================

def login_required(f):
    """Décorateur pour exiger une connexion"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================
# INITIALISATION DU SYSTÈME
# =====================================

def init_system():
    """Initialise le système de recommandation"""
    print("\n" + "🎓"*30)
    print("   SYSTÈME DE RECOMMANDATION DE COURS")
    print("🎓"*30 + "\n")
    
    if os.path.exists('models/recommender_simple.pkl'):
        print("📂 Chargement du modèle existant...")
        recommender.load_model()
        recommender.load_courses()
    else:
        print("🧠 Entraînement d'un nouveau modèle...")
        recommender.train()
        recommender.save_model()
    
    if recommender.is_ready:
        stats = recommender.get_stats()
        print(f"\n✅ Système prêt!")
        print(f"   📊 {stats.get('total_courses', 0)} cours disponibles")
        print(f"   👥 {db.get_total_users()} utilisateurs enregistrés")
        return True
    
    return False

# =====================================
# ROUTES D'AUTHENTIFICATION
# =====================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message = db.login_user(username, password)
        
        if success:
            session['username'] = username
            session.permanent = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error=message)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        
        if len(username) < 3:
            return render_template('register.html', error="Le nom d'utilisateur doit contenir au moins 3 caractères")
        
        if len(password) < 4:
            return render_template('register.html', error="Le mot de passe doit contenir au moins 4 caractères")
        
        if password != confirm:
            return render_template('register.html', error="Les mots de passe ne correspondent pas")
        
        success, message = db.register_user(username, email, password)
        
        if success:
            session['username'] = username
            session.permanent = True
            return redirect(url_for('home'))
        else:
            return render_template('register.html', error=message)
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.pop('username', None)
    return redirect(url_for('login'))

# =====================================
# ROUTES PRINCIPALES
# =====================================

@app.route('/')
@login_required
def home():
    """Page d'accueil avec recommandations personnalisées"""
    username = session.get('username')
    
    user_stats = db.get_user_stats(username)
    user_prefs = db.get_user_preferences(username)
    
    categories = recommender.get_categories()
    platforms = recommender.get_platforms()
    levels = recommender.get_levels()
    stats = recommender.get_stats()
    
    # Génère des recommandations personnalisées
    personalized_courses = []
    reasons = {}
    
    # 1. Basé sur les recherches récentes
    recent_searches = db.get_recent_searches(username, 3)
    for query in recent_searches[:2]:
        if query:
            results = recommender.search_courses(query, n=3)
            for course in results:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    reasons[course['course_id']] = f"Basé sur votre recherche: '{query}'"
    
    # 2. Basé sur les catégories préférées
    top_categories = db.get_top_categories(username, 3)
    for category in top_categories:
        cat_courses = recommender.get_popular_courses(n=3, category=category)
        for course in cat_courses:
            if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                personalized_courses.append(course)
                reasons[course['course_id']] = f"Car vous aimez: {category}"
    
    # 3. Complète avec des cours populaires
    if len(personalized_courses) < 15:
        popular = recommender.get_popular_courses(n=20)
        for course in popular:
            if len(personalized_courses) >= 20:
                break
            if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                personalized_courses.append(course)
                reasons[course['course_id']] = "Cours populaire"
    
    # Ajoute les raisons aux cours
    for course in personalized_courses:
        course['reason'] = reasons.get(course['course_id'], '')
        if 'similarity_score' not in course:
            course['similarity_score'] = 75
    
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
    """Page de liste de tous les cours avec filtres"""
    username = session.get('username')
    
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'rating')
    platform = request.args.get('platform', '')
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    
    filters = {}
    if platform:
        filters['platform'] = platform
    if category:
        filters['category'] = category
    if level:
        filters['level'] = level
    if search:
        filters['search'] = search
    
    result = recommender.get_all_courses(
        page=page,
        per_page=12,
        sort_by=sort_by,
        filters=filters
    )
    
    return render_template('courses.html',
                         username=username,
                         courses=result['courses'],
                         total=result['total'],
                         pages=result['pages'],
                         current_page=page,
                         categories=recommender.get_categories(),
                         platforms=recommender.get_platforms(),
                         levels=recommender.get_levels(),
                         current_filters={
                             'platform': platform,
                             'category': category,
                             'level': level,
                             'search': search,
                             'sort': sort_by
                         })

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """Page de détail d'un cours"""
    username = session.get('username')
    
    course = recommender.get_course_by_id(course_id)
    
    if not course:
        return redirect(url_for('courses'))
    
    db.add_click(username, course)
    
    similar_courses = recommender.find_similar_courses(course_id, n=6)
    
    return render_template('course_detail.html',
                         username=username,
                         course=course,
                         similar_courses=similar_courses)

@app.route('/profile')
@login_required
def profile():
    """Page de profil utilisateur"""
    username = session.get('username')
    
    user = db.get_user(username)
    stats = db.get_user_stats(username)
    prefs = db.get_user_preferences(username)
    
    return render_template('profile.html',
                         username=username,
                         user=user,
                         stats=stats,
                         preferences=prefs)

# =====================================
# API ROUTES
# =====================================

@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API de recherche de cours"""
    username = session.get('username')
    data = request.get_json()
    query = data.get('query', '')
    n = data.get('n', 20)
    
    if not query:
        return jsonify({'error': 'Requête vide'}), 400
    
    db.add_search(username, query)
    results = recommender.search_courses(query, n)
    
    return jsonify({
        'recommendations': results,
        'query': query,
        'count': len(results)
    })

@app.route('/api/recommend/<int:course_id>')
@login_required
def api_recommend(course_id):
    """API pour obtenir des cours similaires"""
    n = request.args.get('n', 6, type=int)
    similar = recommender.find_similar_courses(course_id, n)
    
    return jsonify({
        'course_id': course_id,
        'recommendations': similar,
        'count': len(similar)
    })

@app.route('/api/stats')
def api_stats():
    """API pour obtenir les statistiques du système"""
    return jsonify(recommender.get_stats())

# =====================================
# POINT D'ENTRÉE
# =====================================

if __name__ == '__main__':
    if init_system():
        print(f"\n🚀 Démarrage du serveur Flask...")
        print(f"📍 Accédez à: http://localhost:5000\n")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("\n❌ Impossible de démarrer l'application")
        print("Vérifiez que le fichier data/final_courses.csv existe")
