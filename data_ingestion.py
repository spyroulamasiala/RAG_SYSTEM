"""
Data ingestion module for Help Center articles.

This module defines the Article dataclass and delegates to sample_articles for content loading.
"""
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Article:
    """Represents a Help Center article."""
    url: str
    title: str
    content: str
    metadata: Dict[str, str]


def load_help_center_articles() -> List[Article]:
    """
    Load all Help Center articles specified in the assignment.
    
    Per assignment instructions, we use pre-fetched content instead of active web scraping.
    This delegates to sample_articles.py which contains the actual article content.
    
    Returns:
        List of processed Article objects
    """
    from sample_articles import load_sample_articles
    return load_sample_articles()
