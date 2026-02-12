"""
Scrapers package for Course Recommendation System
"""

from .coursera import CourseraScraper
from .udemy import UdemyScraper

__all__ = ['CourseraScraper', 'UdemyScraper']
