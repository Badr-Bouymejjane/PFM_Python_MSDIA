"""
Système d'Authentification et de Suivi des Utilisateurs (Backend SQLite)
Gère l'inscription, la connexion et le suivi comportemental des utilisateurs via SQLite
"""

from database import Database

class UserManager:
    """Gère les utilisateurs et le suivi de leur comportement via une base de données SQLite"""
    
    def __init__(self, db_path='data/recommandations.db'):
        self.db = Database(db_path)
        
    def register(self, username, email, password):
        """Enregistrer un nouvel utilisateur"""
        return self.db.register_user(username, email, password)
        
    def login(self, username, password):
        """Authentifier un utilisateur"""
        return self.db.login_user(username, password)
        
    def get_user(self, username):
        """Obtenir les infos de l'utilisateur (sans le mot de passe)"""
        return self.db.get_user(username)
        
    def track_search(self, username, query):
        """Suivre une recherche utilisateur"""
        self.db.add_search(username, query)
        
    def track_click(self, username, course):
        """Suivre le clic d'un utilisateur sur un cours"""
        self.db.add_click(username, course)
        
    def track_view(self, username, course_id):
        """Suivre la vue d'un cours"""
        # Nous utilisons les clics pour les préférences, le suivi des vues brutes peut être ajouté à la BD si nécessaire
        pass
        
    def add_favorite(self, username, course_id):
        """Ajouter un cours aux favoris"""
        return self.db.add_favorite(username, course_id)
            
    def remove_favorite(self, username, course_id):
        """Retirer un cours des favoris"""
        return self.db.remove_favorite(username, course_id)
        
    def get_favorites(self, username):
        """Obtenir les cours favoris de l'utilisateur"""
        return self.db.get_favorites(username)
        
    def get_preferences(self, username):
        """Obtenir les préférences de l'utilisateur basées sur son comportement"""
        return self.db.get_user_preferences(username)
        
    def get_top_categories(self, username, n=5):
        """Obtenir les catégories principales de l'utilisateur"""
        return self.db.get_top_categories(username, n)
        
    def get_recent_searches(self, username, n=10):
        """Obtenir les recherches récentes de l'utilisateur"""
        return self.db.get_recent_searches(username, n)
        
    def get_user_stats(self, username):
        """Obtenir les statistiques de l'utilisateur"""
        return self.db.get_user_stats(username)
        
    def get_all_users_count(self):
        """Obtenir le nombre total d'utilisateurs"""
        return self.db.get_total_users()
