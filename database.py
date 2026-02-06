"""
Gestionnaire de base de données SQLite
Gère les utilisateurs et leurs comportements
"""

import sqlite3
import hashlib
from datetime import datetime
import os

class Database:
    """Classe pour gérer la base de données SQLite"""
    
    def __init__(self, db_path='data/recommandations.db'):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Crée une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Crée les tables si elles n'existent pas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        ''')
        
        # Table des recherches
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Table des clics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                course_title TEXT,
                category TEXT,
                level TEXT,
                platform TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Table des favoris
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash un mot de passe avec SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, email, password):
        """Enregistre un nouvel utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_pwd = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed_pwd, datetime.now().isoformat()))
            conn.commit()
            return True, "Inscription réussie"
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return False, "Ce nom d'utilisateur existe déjà"
            else:
                return False, "Cet email existe déjà"
        finally:
            conn.close()
    
    def login_user(self, username, password):
        """Authentifie un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        hashed_pwd = self.hash_password(password)
        cursor.execute('''
            SELECT id FROM users WHERE username = ? AND password = ?
        ''', (username, hashed_pwd))
        
        user = cursor.fetchone()
        
        if user:
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user['id']))
            conn.commit()
            conn.close()
            return True, "Connexion réussie"
        
        conn.close()
        return False, "Nom d'utilisateur ou mot de passe incorrect"
    
    def get_user(self, username):
        """Récupère les informations d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, created_at, last_login
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    
    def get_user_id(self, username):
        """Récupère l'ID d'un utilisateur"""
        user = self.get_user(username)
        return user['id'] if user else None
    
    def add_search(self, username, query):
        """Enregistre une recherche"""
        user_id = self.get_user_id(username)
        if not user_id:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO searches (user_id, query, timestamp)
            VALUES (?, ?, ?)
        ''', (user_id, query, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def add_click(self, username, course):
        """Enregistre un clic sur un cours"""
        user_id = self.get_user_id(username)
        if not user_id:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clicks (user_id, course_id, course_title, category, level, platform, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            course.get('course_id'),
            course.get('title'),
            course.get('category'),
            course.get('level'),
            course.get('platform'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_searches(self, username, limit=10):
        """Récupère les recherches récentes d'un utilisateur"""
        user_id = self.get_user_id(username)
        if not user_id:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query FROM searches
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        searches = [row['query'] for row in cursor.fetchall()]
        conn.close()
        return searches
    
    def get_user_preferences(self, username):
        """Calcule les préférences d'un utilisateur basées sur ses clics"""
        user_id = self.get_user_id(username)
        if not user_id:
            return {'categories': {}, 'levels': {}, 'platforms': {}}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Compte les catégories
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM clicks
            WHERE user_id = ? AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        ''', (user_id,))
        categories = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Compte les niveaux
        cursor.execute('''
            SELECT level, COUNT(*) as count
            FROM clicks
            WHERE user_id = ? AND level IS NOT NULL
            GROUP BY level
            ORDER BY count DESC
        ''', (user_id,))
        levels = {row['level']: row['count'] for row in cursor.fetchall()}
        
        # Compte les plateformes
        cursor.execute('''
            SELECT platform, COUNT(*) as count
            FROM clicks
            WHERE user_id = ? AND platform IS NOT NULL
            GROUP BY platform
            ORDER BY count DESC
        ''', (user_id,))
        platforms = {row['platform']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'categories': categories,
            'levels': levels,
            'platforms': platforms
        }
    
    def get_top_categories(self, username, limit=5):
        """Récupère les catégories préférées d'un utilisateur"""
        prefs = self.get_user_preferences(username)
        categories = prefs['categories']
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return [cat[0] for cat in sorted_cats[:limit]]
    
    def get_user_stats(self, username):
        """Récupère les statistiques d'un utilisateur"""
        user_id = self.get_user_id(username)
        if not user_id:
            return {}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM searches WHERE user_id = ?', (user_id,))
        total_searches = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM clicks WHERE user_id = ?', (user_id,))
        total_clicks = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM favorites WHERE user_id = ?', (user_id,))
        total_favorites = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'total_searches': total_searches,
            'total_clicks': total_clicks,
            'total_favorites': total_favorites,
            'top_categories': self.get_top_categories(username, 3),
            'recent_searches': self.get_recent_searches(username, 5)
        }
    
    def add_favorite(self, username, course_id):
        """Ajoute un cours aux favoris"""
        user_id = self.get_user_id(username)
        if not user_id:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO favorites (user_id, course_id, timestamp)
                VALUES (?, ?, ?)
            ''', (user_id, course_id, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Déjà en favoris
        finally:
            conn.close()
            
    def remove_favorite(self, username, course_id):
        """Supprime un cours des favoris"""
        user_id = self.get_user_id(username)
        if not user_id:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM favorites WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
        
    def get_favorites(self, username):
        """Récupère la liste des IDs des cours favoris"""
        user_id = self.get_user_id(username)
        if not user_id:
            return []
            
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT course_id FROM favorites WHERE user_id = ?', (user_id,))
        favs = [row['course_id'] for row in cursor.fetchall()]
        conn.close()
        return favs

    def get_total_users(self):
        """Récupère le nombre total d'utilisateurs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users')
        count = cursor.fetchone()['count']
        
        conn.close()
        return count
