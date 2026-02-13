"""
Système d'Authentification et de Suivi des Utilisateurs (Backend SQLite)
Gère l'inscription, la connexion et le suivi comportemental des utilisateurs via SQLite
"""

# === IMPORTATIONS ===
from database import Database  # Import de la classe de gestion de base de données SQLite

# === CLASSE PRINCIPALE ===
class UserManager:  # Contrôleur qui gère la logique utilisateur et interagit avec la BDD
    """Gère les utilisateurs et le suivi de leur comportement via une base de données SQLite"""
    
    def __init__(self, db_path='data/recommandations.db'):
        """Initialise le gestionnaire d'utilisateurs avec une connexion à la base de données"""
        # Initialise la connexion à la base de données SQLite
        # Le fichier DB sera créé automatiquement s'il n'existe pas
        # db_path : chemin vers le fichier de base de données (par défaut : data/recommandations.db)
        self.db = Database(db_path)  # Crée une instance de la classe Database
        
    # === GESTION DES COMPTES UTILISATEURS ===
    # Ces méthodes gèrent l'authentification et la création de comptes
    
    def register(self, username, email, password):
        """Enregistrer un nouvel utilisateur dans la base de données"""
        # Appelle la méthode de la base de données pour créer l'utilisateur
        # Le mot de passe sera hashé (bcrypt) avant d'être stocké (sécurité)
        # Retourne (succès: bool, message: str) pour gérer les erreurs (ex: pseudo déjà pris)
        return self.db.register_user(username, email, password)
        
    def login(self, username, password):
        """Authentifier un utilisateur (vérification des identifiants)"""
        # Vérifie les identifiants hashés dans la base de données
        # Compare le mot de passe fourni avec le hash stocké (bcrypt.checkpw)
        # Retourne (succès: bool, message: str)
        return self.db.login_user(username, password)
        
    def get_user(self, username):
        """Obtenir les informations complètes de l'utilisateur (sans le mot de passe)"""
        # Récupère les données utilisateur depuis la table 'users'
        # Retourne un dictionnaire avec : username, email, created_at, etc.
        # Le mot de passe hashé n'est PAS inclus (sécurité)
        return self.db.get_user(username)
        
    # === SUIVI COMPORTEMENTAL (TRACKING) ===
    # Ces méthodes enregistrent les actions de l'utilisateur pour personnaliser les recommandations
    
    def track_search(self, username, query):
        """Suivre une recherche utilisateur (enregistrement dans la table 'searches')"""
        # Enregistre le terme recherché avec un timestamp (horodatage)
        # Utilisé pour améliorer les futures recommandations (intentions explicites)
        # Exemple : si l'utilisateur cherche "Python", on lui recommandera des cours Python
        self.db.add_search(username, query)
        
    def track_click(self, username, course):
        """Suivre le clic d'un utilisateur sur un cours (enregistrement dans la table 'clicks')"""
        # Enregistre l'interaction avec un cours spécifique
        # Stocke : course_id, category, platform, rating, timestamp
        # Permet de construire le profil d'intérêts de l'utilisateur (comportement implicite)
        # Exemple : si l'utilisateur clique souvent sur "Data Science", cette catégorie devient une préférence
        self.db.add_click(username, course)
        
    def track_view(self, username, course_id):
        """Suivre la vue d'un cours (consultation de la page de détail)"""
        # Actuellement non implémenté dans la base de données (pass = ne fait rien)
        # Nous utilisons les clics pour les préférences, le suivi des vues brutes peut être ajouté à la BD si nécessaire
        # Cette méthode existe pour la compatibilité future (extensibilité)
        pass
        
    # === GESTION DES FAVORIS ===
    # Permet aux utilisateurs de marquer des cours comme favoris (liste de souhaits)
    
    def add_favorite(self, username, course_id):
        """Ajouter un cours aux favoris de l'utilisateur (table 'favorites')"""
        # Insère une entrée dans la table 'favorites' avec username + course_id
        # Retourne True si succès, False si erreur (ex: déjà dans les favoris)
        return self.db.add_favorite(username, course_id)
            
    def remove_favorite(self, username, course_id):
        """Retirer un cours des favoris de l'utilisateur"""
        # Supprime l'entrée correspondante de la table 'favorites'
        # Retourne True si succès, False si erreur
        return self.db.remove_favorite(username, course_id)
        
    def get_favorites(self, username):
        """Obtenir la liste des cours favoris de l'utilisateur"""
        # Récupère tous les course_id marqués comme favoris pour cet utilisateur
        # Retourne une liste d'IDs de cours : [123, 456, 789, ...]
        return self.db.get_favorites(username)
        
    # === ANALYSE DES PRÉFÉRENCES UTILISATEUR ===
    # Ces méthodes analysent le comportement pour identifier les intérêts de l'utilisateur
    
    def get_preferences(self, username):
        """Obtenir les préférences de l'utilisateur basées sur son comportement"""
        # Analyse l'historique des clics pour déterminer les catégories favorites
        # Compte le nombre de clics par catégorie (ex: {"Data Science": 15, "Web Development": 8, ...})
        # Retourne un dictionnaire avec les compteurs par catégorie
        # Utilisé pour personnaliser les recommandations (plus de clics = plus d'intérêt)
        return self.db.get_user_preferences(username)
        
    def get_top_categories(self, username, n=5):
        """Obtenir les catégories principales de l'utilisateur (top N)"""
        # Identifie les N catégories les plus consultées par l'utilisateur
        # Retourne une liste triée par ordre décroissant : ["Data Science", "AI", "Python", ...]
        # Paramètre n : nombre de catégories à retourner (par défaut 5)
        return self.db.get_top_categories(username, n)
        
    def get_recent_searches(self, username, n=10):
        """Obtenir les recherches récentes de l'utilisateur (historique)"""
        # Récupère les N dernières recherches effectuées (triées par date décroissante)
        # Retourne une liste de chaînes : ["machine learning", "python", "data analysis", ...]
        # Utilisé pour les suggestions et les recommandations contextuelles
        # Paramètre n : nombre de recherches à retourner (par défaut 10)
        return self.db.get_recent_searches(username, n)
        
    def get_user_stats(self, username):
        """Obtenir les statistiques d'activité de l'utilisateur"""
        # Récupère des métriques d'engagement : nombre de clics, recherches, favoris, etc.
        # Retourne un dictionnaire : {"total_clicks": 42, "total_searches": 18, "total_favorites": 5, ...}
        # Utilisé pour afficher le profil utilisateur et mesurer l'engagement
        return self.db.get_user_stats(username)
        
    def get_all_users_count(self):
        """Obtenir le nombre total d'utilisateurs inscrits dans le système"""
        # Compte le nombre total d'entrées dans la table 'users'
        # Retourne un entier : nombre d'utilisateurs (ex: 127)
        # Utilisé pour les statistiques globales du système
        return self.db.get_total_users()

    # === PARCOURS D'APPRENTISSAGE (LEARNING PATHS) ===
    # Permet de sauvegarder et récupérer des parcours d'apprentissage personnalisés
    
    def save_path(self, username, category, path_data):
        """Sauvegarder un parcours d'apprentissage pour l'utilisateur"""
        # Sauvegarde un chemin d'apprentissage généré par le clustering pour consultation ultérieure
        # path_data : liste de cours organisés par niveau (Débutant -> Avancé), stockée au format JSON
        # Exemple : {"category": "Data Science", "courses": [{"id": 1, "title": "...", "level": "Beginner"}, ...]}
        # Permet à l'utilisateur de retrouver ses parcours sauvegardés dans son profil
        return self.db.add_saved_path(username, category, path_data)
        
    def get_saved_paths(self, username):
        """Obtenir tous les parcours d'apprentissage sauvegardés par l'utilisateur"""
        # Récupère la liste de tous les parcours enregistrés (table 'saved_paths')
        # Retourne une liste de dictionnaires : [{"category": "...", "path_data": {...}, "created_at": "..."}, ...]
        # Utilisé pour afficher les parcours dans la page de profil
        return self.db.get_saved_paths(username)
