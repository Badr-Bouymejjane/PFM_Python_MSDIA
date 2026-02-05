"""
Generate Sample Data - Creates example course data for testing
Useful when scraping is not possible or for quick testing
"""

import sys
import os

# Configuration UTF-8 pour Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import random

from config import RAW_DATA_PATH, CATEGORIES


def generate_sample_data(num_courses=500):
    """Generate sample course data for both platforms"""
    
    print("\n" + "="*60)
    print("   📦 GÉNÉRATION DE DONNÉES D'EXEMPLE")
    print("="*60 + "\n")
    
    # Course templates
    course_templates = {
        'Data Science': [
            ("Complete Data Science Bootcamp", "Learn data science from scratch. Python, SQL, Machine Learning, Deep Learning, and more."),
            ("Data Science Fundamentals", "Master the fundamentals of data science with hands-on projects."),
            ("Data Analysis with Python", "Learn to analyze data using Python pandas, numpy, and visualization tools."),
            ("Data Science for Business", "Apply data science techniques to solve real business problems."),
            ("Advanced Data Science", "Take your data science skills to the next level with advanced techniques."),
        ],
        'Machine Learning': [
            ("Machine Learning A-Z", "Complete Machine Learning and Data Science course with Python and R."),
            ("Machine Learning Fundamentals", "Master machine learning algorithms with practical examples."),
            ("Applied Machine Learning", "Learn to apply ML to real-world problems."),
            ("Machine Learning with Python", "Build ML models using Python and scikit-learn."),
            ("Machine Learning Engineering", "Production-ready machine learning systems."),
        ],
        'Artificial Intelligence': [
            ("AI for Everyone", "Learn what AI is and how it's transforming industries."),
            ("Artificial Intelligence Fundamentals", "Master the basics of AI and its applications."),
            ("AI and Machine Learning", "Comprehensive guide to AI and ML technologies."),
            ("AI for Business", "Learn how to apply AI in business contexts."),
            ("Advanced AI Techniques", "Deep dive into advanced AI methodologies."),
        ],
        'Deep Learning': [
            ("Deep Learning Specialization", "Master deep learning and neural networks."),
            ("Deep Learning with TensorFlow", "Build neural networks with TensorFlow."),
            ("Deep Learning with PyTorch", "Create deep learning models using PyTorch."),
            ("Neural Networks from Scratch", "Understand neural networks by building them from scratch."),
            ("Applied Deep Learning", "Real-world deep learning applications."),
        ],
        'Python Programming': [
            ("Python for Beginners", "Learn Python programming from zero to hero."),
            ("Complete Python Masterclass", "Master Python with hands-on projects."),
            ("Python for Data Science", "Use Python for data analysis and visualization."),
            ("Advanced Python Programming", "Advanced Python concepts and best practices."),
            ("Python Automation", "Automate tasks with Python scripts."),
        ],
        'Web Development': [
            ("Full Stack Web Development", "Learn frontend and backend web development."),
            ("HTML, CSS, and JavaScript", "Master the fundamentals of web development."),
            ("React - The Complete Guide", "Build modern web apps with React."),
            ("Node.js Developer Course", "Backend development with Node.js and Express."),
            ("Web Development Bootcamp", "Comprehensive web development training."),
        ],
        'Cloud Computing': [
            ("AWS Certified Solutions Architect", "Prepare for AWS certification."),
            ("Google Cloud Platform Fundamentals", "Learn GCP from scratch."),
            ("Microsoft Azure Fundamentals", "Master Azure cloud services."),
            ("Cloud Computing Essentials", "Understanding cloud computing concepts."),
            ("DevOps with Cloud", "Implement DevOps practices in the cloud."),
        ],
        'Cybersecurity': [
            ("Cybersecurity Fundamentals", "Learn the basics of cybersecurity."),
            ("Ethical Hacking", "Master ethical hacking techniques."),
            ("Network Security", "Secure networks against cyber threats."),
            ("Information Security", "Protect information systems and data."),
            ("Security+", "Prepare for CompTIA Security+ certification."),
        ],
        'Business': [
            ("Business Strategy", "Develop effective business strategies."),
            ("Project Management Professional", "Master project management skills."),
            ("Lean Six Sigma", "Learn process improvement methodologies."),
            ("Business Analytics", "Use data to drive business decisions."),
            ("Entrepreneurship", "Start and grow your own business."),
        ],
        'Marketing': [
            ("Digital Marketing Complete Course", "Master all aspects of digital marketing."),
            ("Social Media Marketing", "Learn to market on social platforms."),
            ("SEO Masterclass", "Optimize websites for search engines."),
            ("Content Marketing", "Create and distribute valuable content."),
            ("Email Marketing", "Build effective email campaigns."),
        ],
    }
    
    # Instructors
    instructors = {
        'Coursera': [
            "Andrew Ng", "Dr. Angela Yu", "Jose Portilla", "IBM", "Google",
            "University of Michigan", "Stanford University", "DeepLearning.AI",
            "Duke University", "Johns Hopkins University", "Meta", "Microsoft"
        ],
        'Udemy': [
            "Jose Portilla", "Colt Steele", "Angela Yu", "Stephen Grider",
            "Maximilian Schwarzmüller", "Brad Traversy", "Tim Buchalka",
            "Rob Percival", "Jonas Schmedtmann", "Andrei Neagoie"
        ]
    }
    
    # Levels
    levels = ['Beginner', 'Intermediate', 'Advanced', 'All Levels']
    
    # Prices
    coursera_prices = ['Subscription', 'Free', 'Subscription', 'Subscription']
    udemy_prices = ['$12.99', '$19.99', '$49.99', '$84.99', 'Free', '$9.99']
    
    # Generate courses
    courses = []
    course_id = 1
    
    # Map categories
    category_map = {
        'data-science': 'Data Science',
        'machine-learning': 'Machine Learning',
        'artificial-intelligence': 'Artificial Intelligence',
        'deep-learning': 'Deep Learning',
        'python': 'Python Programming',
        'web-development': 'Web Development',
        'cloud-computing': 'Cloud Computing',
        'cybersecurity': 'Cybersecurity',
        'business': 'Business',
        'marketing': 'Marketing',
    }
    
    for platform in ['Coursera', 'Udemy']:
        for config_cat in CATEGORIES:
            category = category_map.get(config_cat, config_cat.replace('-', ' ').title())
            
            if category not in course_templates:
                continue
                
            templates = course_templates[category]
            
            for i, (title_template, desc_template) in enumerate(templates):
                # Create variations
                for variant in range(3):
                    title = title_template
                    if variant == 1:
                        title = f"The Complete {title}"
                    elif variant == 2:
                        title = f"{title} - From Zero to Expert"
                        
                    course = {
                        'course_id': course_id,
                        'platform': platform,
                        'title': title,
                        'description': desc_template + f" Join thousands of students who have transformed their careers. Updated for {datetime.now().year}.",
                        'category': category,
                        'skills': f"{category.lower()}, programming, analysis, problem solving",
                        'instructor': random.choice(instructors[platform]),
                        'rating': round(random.uniform(4.0, 5.0), 1),
                        'num_reviews': random.randint(500, 100000),
                        'price': random.choice(coursera_prices if platform == 'Coursera' else udemy_prices),
                        'level': random.choice(levels),
                        'language': 'English',
                        'duration': f"{random.randint(10, 100)} hours",
                        'url': f"https://www.{platform.lower()}.org/course/{config_cat}-{course_id}",
                        'image_url': '',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    courses.append(course)
                    course_id += 1
                    
                    if len(courses) >= num_courses:
                        break
                        
                if len(courses) >= num_courses:
                    break
                    
            if len(courses) >= num_courses:
                break
                
        if len(courses) >= num_courses:
            break
    
    # Create DataFrame
    df = pd.DataFrame(courses)
    
    # Save
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False, encoding='utf-8')
    
    print(f"✅ {len(df)} cours générés")
    print(f"   📊 Coursera: {len(df[df['platform'] == 'Coursera'])} cours")
    print(f"   📊 Udemy: {len(df[df['platform'] == 'Udemy'])} cours")
    print(f"   📊 Catégories: {df['category'].nunique()}")
    print(f"\n💾 Sauvegardé: {RAW_DATA_PATH}")
    
    return df


if __name__ == "__main__":
    generate_sample_data(500)
