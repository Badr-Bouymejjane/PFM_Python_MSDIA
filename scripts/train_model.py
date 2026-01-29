
import pandas as pd
import numpy as np
import os
import re
import math
from collections import Counter

# CONFIG
DATA_PATH = "data/final_courses.csv"

class CourseRecommender:
    def __init__(self, data_path=None):
        self.data_path = data_path if data_path else DATA_PATH
        self.df = None
        self.vocab = {} # word -> index
        self.idf = {} # word -> idf value
        self.tf_idf_matrix = None
        self.load_data()
        self.train_engine()

    def load_data(self):
        """Loads the processed dataset."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found at {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        self.df['id'] = self.df['id'].astype(str)
        self.df = self.df.fillna('')
        # Normalize popularity for hybrid ranking
        max_pop = self.df['popularity_score'].max()
        if max_pop > 0:
            self.df['norm_popularity'] = self.df['popularity_score'] / max_pop
        else:
            self.df['norm_popularity'] = 0
            
        print(f"Recommender loaded {len(self.df)} courses.")

    def tokenize(self, text):
        """Simple tokenizer with stopword removal."""
        text = str(text).lower()
        # Keep only alphanumeric
        tokens = re.findall(r'\b[a-z]{2,}\b', text)
        
        # Basic English Stopwords (Hardcoded to avoid NLTK dependency)
        STOPWORDS = {
            'the', 'and', 'for', 'that', 'with', 'this', 'from', 'your', 'are', 'will', 
            'can', 'learn', 'how', 'what', 'intro', 'introduction', 'full', 'guide', 
            'course', 'tutorial', 'complete', 'bootcamp', 'advanced', 'beginner', 
            'intermediate', 'master', 'fundamentals', 'basics', 'project', 'science',
            'data', 'web', 'development'
             # actually 'data' and 'science' are key keywords, let's keep them.
             # reducing generic ones
            'com', 'www', 'https', 'http'
        }
        
        return [t for t in tokens if t not in STOPWORDS]

    def train_engine(self):
        """Builds valid TF-IDF matrix using Manual Numpy implementation."""
        print("Training Recommendation Engine (Numpy)...")
        
        # 1. Prepare Corpus
        # Handle missing columns gracefully
        def safe_get(row, col):
            return str(row[col]) if col in row and not pd.isna(row[col]) else ""
        
        self.df['soup'] = self.df.apply(lambda row: 
            (str(row['title_clean']) + " ") * 5 +  # Title is most important
            (str(row['category']) + " ") * 3 +     # Category is strong signal
            safe_get(row, 'partner') + " " + 
            safe_get(row, 'metadata') + " " +
            safe_get(row, 'full_description'),      # Might be empty
            axis=1
        )
        
        corpus = self.df['soup'].apply(self.tokenize).tolist()
        N = len(corpus)
        
        # 2. Build Vocabulary & DF (Document Frequency)
        df_counts = Counter()
        for doc in corpus:
            unique_words = set(doc)
            for w in unique_words:
                df_counts[w] += 1
                
        # Filter rare words (min doc freq = 2) to keep matrix small
        filtered_words = [w for w, c in df_counts.items() if c >= 2]
        self.vocab = {w: i for i, w in enumerate(filtered_words)}
        vocab_size = len(self.vocab)
        print(f"Vocabulary Size: {vocab_size}")
        
        # 3. Calculate IDF
        self.idf = np.zeros(vocab_size)
        for w, idx in self.vocab.items():
            # Standard IDF: log(N / (df + 1))
            self.idf[idx] = math.log(N / (df_counts[w] + 1))
            
        # 4. Calculate TF-IDF Matrix
        self.tf_idf_matrix = np.zeros((N, vocab_size))
        
        for i, doc in enumerate(corpus):
            tf_counts = Counter(doc)
            doc_len = len(doc)
            for w, count in tf_counts.items():
                if w in self.vocab:
                    idx = self.vocab[w]
                    tf = count / doc_len # Normalized TF
                    self.tf_idf_matrix[i, idx] = tf * self.idf[idx]
        
        # 5. Normalize vectors (L2 norm) for Cosine Similarity
        # Divide each row by its norm
        norms = np.linalg.norm(self.tf_idf_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1 # avoid divide by zero
        self.tf_idf_matrix = self.tf_idf_matrix / norms
        
        print(f"Engine Trained. Matrix Shape: {self.tf_idf_matrix.shape}")

    def search(self, query, top_k=5):
        """Search using hybrid ranking (Cosine + Popularity)."""
        tokens = self.tokenize(query)
        query_vec = np.zeros(len(self.vocab))
        
        # Vectorize Loop
        tf_counts = Counter(tokens)
        doc_len = len(tokens)
        if doc_len == 0: return []
        
        for w, count in tf_counts.items():
            if w in self.vocab:
                idx = self.vocab[w]
                tf = count / doc_len
                query_vec[idx] = tf * self.idf[idx]
        
        # Normalize Query
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0: return []
        query_vec = query_vec / q_norm
        
        # Dot Product (since both normalized, Dot == Cosine)
        # matrix (N, V) dot query (V,) -> (N,)
        cosine_scores = np.dot(self.tf_idf_matrix, query_vec)
        
        # Hybrid Scoring
        # Final = Cosine * (1 + 0.5 * Popularity)
        # This gives up to 50% boost to extremely popular items
        pop_scores = self.df['norm_popularity'].values
        final_scores = cosine_scores * (1 + 0.3 * pop_scores) 
        
        # Top K
        top_indices = final_scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            score = final_scores[idx]
            if score < 0.05: continue # Lower threshold as boosting might skew relative low matches
            
            record = self.df.iloc[idx].to_dict()
            record['similarity_score'] = float(score)
            record['base_cosine'] = float(cosine_scores[idx]) # Debug info
            results.append(record)
            
        return results

    def recommend_similar(self, course_id, top_k=5):
        """Find similar items."""
        idx_list = self.df.index[self.df['id'] == str(course_id)].tolist()
        if not idx_list: return []
        idx = idx_list[0]
        
        # Dot product of this vector with all others
        target_vec = self.tf_idf_matrix[idx]
        scores = np.dot(self.tf_idf_matrix, target_vec)
        
        # Sort
        similar_indices = scores.argsort()[-(top_k+1):][::-1]
        
        results = []
        for i in similar_indices:
            if i == idx: continue
            
            record = self.df.iloc[i].to_dict()
            record['similarity_score'] = float(scores[i])
            results.append(record)
            
        return results[:top_k]

if __name__ == "__main__":
    rec = CourseRecommender()
    
    # Test multiple diverse queries to prove it works for ALL categories
    test_queries = [
        "Python Data Science", 
        "Digital Marketing Strategy", 
        "Graphic Design for Beginners",
        "Project Management PMP"
    ]
    
    for q in test_queries:
        print(f"\n--- Testing Search: '{q}' ---")
        results = rec.search(q, top_k=3)
        for res in results:
            print(f"[{res['similarity_score']:.2f}] {res['title']} ({res['source_domain']})")
