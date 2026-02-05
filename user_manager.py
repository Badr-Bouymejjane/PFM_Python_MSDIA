"""
User Authentication and Tracking System
Handles user registration, login, and behavior tracking
"""

import os
import json
import hashlib
from datetime import datetime
from collections import defaultdict


class UserManager:
    """Manages users and their behavior tracking"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, 'users.json')
        self.behaviors_file = os.path.join(data_dir, 'user_behaviors.json')
        self.users = {}
        self.behaviors = {}
        self.load_data()
        
    def load_data(self):
        """Load users and behaviors from files"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
                
        if os.path.exists(self.behaviors_file):
            with open(self.behaviors_file, 'r', encoding='utf-8') as f:
                self.behaviors = json.load(f)
                
    def save_data(self):
        """Save users and behaviors to files"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)
            
        with open(self.behaviors_file, 'w', encoding='utf-8') as f:
            json.dump(self.behaviors, f, indent=2, ensure_ascii=False)
            
    def hash_password(self, password):
        """Hash password with SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def register(self, username, email, password):
        """Register a new user"""
        if username in self.users:
            return False, "Username already exists"
            
        for user in self.users.values():
            if user.get('email') == email:
                return False, "Email already exists"
                
        self.users[username] = {
            'email': email,
            'password': self.hash_password(password),
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.behaviors[username] = {
            'searches': [],
            'clicks': [],
            'views': [],
            'favorites': [],
            'preferences': {
                'categories': {},
                'levels': {},
                'platforms': {}
            }
        }
        
        self.save_data()
        return True, "Registration successful"
        
    def login(self, username, password):
        """Authenticate user"""
        if username not in self.users:
            return False, "User not found"
            
        if self.users[username]['password'] != self.hash_password(password):
            return False, "Invalid password"
            
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_data()
        return True, "Login successful"
        
    def get_user(self, username):
        """Get user info (without password)"""
        if username not in self.users:
            return None
        user = self.users[username].copy()
        del user['password']
        return user
        
    def track_search(self, username, query):
        """Track user search"""
        if username not in self.behaviors:
            self.behaviors[username] = {'searches': [], 'clicks': [], 'views': [], 'favorites': [], 'preferences': {'categories': {}, 'levels': {}, 'platforms': {}}}
            
        self.behaviors[username]['searches'].append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 100 searches
        self.behaviors[username]['searches'] = self.behaviors[username]['searches'][-100:]
        self.save_data()
        
    def track_click(self, username, course):
        """Track user click on a course"""
        if username not in self.behaviors:
            return
            
        self.behaviors[username]['clicks'].append({
            'course_id': course.get('course_id'),
            'title': course.get('title'),
            'category': course.get('category'),
            'level': course.get('level'),
            'platform': course.get('platform'),
            'timestamp': datetime.now().isoformat()
        })
        
        # Update preferences
        prefs = self.behaviors[username]['preferences']
        
        cat = course.get('category', 'Other')
        prefs['categories'][cat] = prefs['categories'].get(cat, 0) + 1
        
        level = course.get('level', 'All Levels')
        prefs['levels'][level] = prefs['levels'].get(level, 0) + 1
        
        platform = course.get('platform', 'Unknown')
        prefs['platforms'][platform] = prefs['platforms'].get(platform, 0) + 1
        
        # Keep last 200 clicks
        self.behaviors[username]['clicks'] = self.behaviors[username]['clicks'][-200:]
        self.save_data()
        
    def track_view(self, username, course_id):
        """Track course view"""
        if username not in self.behaviors:
            return
            
        self.behaviors[username]['views'].append({
            'course_id': course_id,
            'timestamp': datetime.now().isoformat()
        })
        
        self.behaviors[username]['views'] = self.behaviors[username]['views'][-200:]
        self.save_data()
        
    def add_favorite(self, username, course_id):
        """Add course to favorites"""
        if username not in self.behaviors:
            return False
            
        if course_id not in self.behaviors[username]['favorites']:
            self.behaviors[username]['favorites'].append(course_id)
            self.save_data()
            return True
        return False
        
    def remove_favorite(self, username, course_id):
        """Remove course from favorites"""
        if username not in self.behaviors:
            return False
            
        if course_id in self.behaviors[username]['favorites']:
            self.behaviors[username]['favorites'].remove(course_id)
            self.save_data()
            return True
        return False
        
    def get_favorites(self, username):
        """Get user's favorite courses"""
        if username not in self.behaviors:
            return []
        return self.behaviors[username].get('favorites', [])
        
    def get_preferences(self, username):
        """Get user preferences based on behavior"""
        if username not in self.behaviors:
            return {}
        return self.behaviors[username].get('preferences', {})
        
    def get_top_categories(self, username, n=5):
        """Get user's top categories"""
        prefs = self.get_preferences(username)
        cats = prefs.get('categories', {})
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_cats[:n]]
        
    def get_recent_searches(self, username, n=10):
        """Get user's recent searches"""
        if username not in self.behaviors:
            return []
        searches = self.behaviors[username].get('searches', [])
        return [s['query'] for s in searches[-n:]]
        
    def get_user_stats(self, username):
        """Get user statistics"""
        if username not in self.behaviors:
            return {}
            
        behavior = self.behaviors[username]
        return {
            'total_searches': len(behavior.get('searches', [])),
            'total_clicks': len(behavior.get('clicks', [])),
            'total_views': len(behavior.get('views', [])),
            'total_favorites': len(behavior.get('favorites', [])),
            'top_categories': self.get_top_categories(username, 3),
            'recent_searches': self.get_recent_searches(username, 5)
        }
        
    def get_all_users_count(self):
        """Get total number of users"""
        return len(self.users)
