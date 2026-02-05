"""
Course Recommendation System - Flask Web Application
With User Authentication and Personalized Recommendations
"""

import sys
import os

# Configuration UTF-8 pour Windows
import io
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        pass

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

# =====================================
# FLASK APP INITIALIZATION
# =====================================

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=SESSION_LIFETIME_DAYS)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Global functions for Jinja templates
app.jinja_env.globals.update(max=max, min=min)

# =====================================
# GLOBAL VARIABLES
# =====================================

recommender = CourseRecommender()
user_manager = UserManager()

# =====================================
# DECORATORS
# =====================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    return session.get('username')

# =====================================
# INIT
# =====================================

def init_recommender():
    global recommender
    
    print("\n" + "🎓"*25)
    print("   COURSE RECOMMENDATION SYSTEM")
    print("🎓"*25 + "\n")
    
    if os.path.exists('models/recommender.pkl'):
        print("📂 Chargement du modèle existant...")
        recommender.load_model()
        recommender.load_data()
    else:
        print("🧠 Entraînement du modèle...")
        recommender.train()
        recommender.save_model()
        
    if recommender.is_trained:
        stats = recommender.get_stats()
        print(f"\n✅ Système prêt!")
        print(f"   📊 {stats.get('total_courses', 0)} cours chargés")
        print(f"   📊 Utilisateurs: {user_manager.get_all_users_count()}")
        return True
    return False

# =====================================
# AUTH ROUTES
# =====================================

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

# =====================================
# WEB ROUTES
# =====================================

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
    
    # Build personalized recommendations
    personalized_courses = []
    recommendation_reasons = {}
    
    # 1. Recommendations based on recent searches
    recent_searches = user_manager.get_recent_searches(username, 3)
    for query in recent_searches[:2]:
        if query:
            search_recs = recommender.recommend_by_query(query, n=3)
            for course in search_recs:
                if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                    personalized_courses.append(course)
                    recommendation_reasons[course['course_id']] = f"Basé sur votre recherche: '{query}'"
    
    # 2. Recommendations based on preferred categories
    top_cats = user_manager.get_top_categories(username, 3)
    for cat in top_cats:
        cat_courses = recommender.get_popular_courses(n=3, category=cat)
        for course in cat_courses:
            if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                personalized_courses.append(course)
                recommendation_reasons[course['course_id']] = f"Car vous aimez: {cat}"
    
    # 3. Fill with popular courses if needed
    if len(personalized_courses) < 15:
        popular = recommender.get_popular_courses(n=25)
        for course in popular:
            if len(personalized_courses) >= 25:
                break
            if course['course_id'] not in [c['course_id'] for c in personalized_courses]:
                personalized_courses.append(course)
                recommendation_reasons[course['course_id']] = "Cours populaire"
    
    # Add reasons and similarity scores to courses
    for course in personalized_courses:
        course['reason'] = recommendation_reasons.get(course['course_id'], '')
        # Add similarity_score if not present (for display purposes)
        if 'similarity_score' not in course or course['similarity_score'] is None:
            # Calculate a score based on rating and reason type
            base_score = 70
            if 'recherche' in course['reason'].lower():
                base_score = 90
            elif 'aimez' in course['reason'].lower():
                base_score = 85
            elif 'populaire' in course['reason'].lower():
                base_score = 75
            
            # Adjust by rating
            rating = course.get('rating', 0)
            if rating >= 4.5:
                base_score += 5
            elif rating >= 4.0:
                base_score += 3
            
            course['similarity_score'] = min(95, base_score)
    
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
    sort_by = request.args.get('sort', 'rating')
    platform = request.args.get('platform', '')
    category = request.args.get('category', '')
    level = request.args.get('level', '')
    search = request.args.get('search', '')
    
    filters = {}
    if platform: filters['platform'] = platform
    if category: filters['category'] = category
    if level: filters['level'] = level
    if search: filters['search'] = search
        
    result = recommender.get_all_courses(
        page=page, per_page=COURSES_PER_PAGE,
        sort_by=sort_by, filters=filters
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
                         current_filters={'platform': platform, 'category': category, 'level': level, 'search': search, 'sort': sort_by})

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    username = get_current_user()
    course = recommender.get_course_by_id(course_id)
    
    if not course:
        return redirect(url_for('courses'))
    
    # Track view
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
    stats = user_manager.get_user_stats(username)
    prefs = user_manager.get_preferences(username)
    
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
    username = get_current_user()
    data = request.get_json()
    query = data.get('query', '')
    n = data.get('n', 20)
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Track search
    user_manager.track_search(username, query)
    
    recommendations = recommender.recommend_by_query(query, n)
    
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

# =====================================
# CLUSTERING ROUTES
# =====================================

clustering_instance = None

def get_clustering():
    global clustering_instance
    if clustering_instance is None:
        from models.clustering import CourseClustering
        clustering_instance = CourseClustering(n_clusters=8)
        clustering_instance.run()
    return clustering_instance

@app.route('/clustering')
@login_required
def clustering():
    import json
    clustering_model = get_clustering()
    viz_data = clustering_model.get_visualization_data()
    clusters_info = clustering_model.get_cluster_info()
    categories = recommender.get_categories()
    
    cluster_colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']
    
    return render_template('clustering.html',
                         username=get_current_user(),
                         viz_data=json.dumps(viz_data),
                         clusters_info=clusters_info,
                         cluster_colors=cluster_colors,
                         categories=categories,
                         total_courses=len(clustering_model.df),
                         n_clusters=8,
                         n_categories=len(categories))


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

# =====================================
# MAIN
# =====================================

if __name__ == '__main__':
    if init_recommender():
        print(f"\n🚀 Démarrage du serveur Flask...")
        print(f"📍 Accédez à: http://localhost:2400\n")
        app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=2400)
    else:
        print("\n❌ Impossible de démarrer l'application")
