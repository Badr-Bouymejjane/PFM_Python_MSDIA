"""
User Authentication and Tracking System (SQLite Backend)
Handles user registration, login, and behavior tracking using SQLite
"""

from database import Database

class UserManager:
    """Manages users and their behavior tracking using a SQLite database"""
    
    def __init__(self, db_path=None):
        self.db = Database(db_path)
        
    def register(self, username, email, password):
        """Register a new user"""
        return self.db.register_user(username, email, password)
        
    def login(self, username, password):
        """Authenticate user"""
        return self.db.login_user(username, password)
        
    def get_user(self, username):
        """Get user info (without password)"""
        return self.db.get_user(username)
        
    def track_search(self, username, query):
        """Track user search"""
        self.db.add_search(username, query)
        
    def track_click(self, username, course):
        """Track user click on a course"""
        self.db.add_click(username, course)
        
    def track_view(self, username, course_id):
        """Track course view"""
        # We use clicks for preferences, tracking raw views can be added to DB if needed
        pass
        
    def add_favorite(self, username, course_id):
        """Add course to favorites"""
        return self.db.add_favorite(username, course_id)
            
    def remove_favorite(self, username, course_id):
        """Remove course from favorites"""
        return self.db.remove_favorite(username, course_id)
        
    def get_favorites(self, username):
        """Get user's favorite courses"""
        return self.db.get_favorites(username)
        
    def get_preferences(self, username):
        """Get user preferences based on behavior"""
        return self.db.get_user_preferences(username)
        
    def get_top_categories(self, username, n=5):
        """Get user's top categories"""
        return self.db.get_top_categories(username, n)
        
    def get_recent_searches(self, username, n=10):
        """Get user's recent searches"""
        return self.db.get_recent_searches(username, n)
        
    def get_user_stats(self, username):
        """Get user statistics"""
        return self.db.get_user_stats(username)
        
    def get_all_users_count(self):
        """Get total number of users"""
        return self.db.get_total_users()
