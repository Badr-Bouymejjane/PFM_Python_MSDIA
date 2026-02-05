"""
Scrapers package for Course Recommendation System
"""

from .coursera_scraper import CourseraScraper
from .udemy_scraper import UdemyScraper

__all__ = ['CourseraScraper', 'UdemyScraper']
