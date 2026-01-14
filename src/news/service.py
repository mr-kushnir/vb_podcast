"""
News Collection Service
Orchestrates news fetching, parsing, and caching
"""

import httpx
from typing import List
from datetime import datetime

from src.news.parser import TechCrunchParser
from src.models.episode import Article
from src.common.config import get_settings

settings = get_settings()

class NewsService:
    """Service for collecting AI news"""

    def __init__(self):
        self.parser = TechCrunchParser()
        self.base_url = "https://techcrunch.com/category/artificial-intelligence/"

    async def collect_latest(self, hours: int = 24) -> List[Article]:
        """Collect latest AI news from TechCrunch"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url)
                response.raise_for_status()

                # Parse all articles from page
                articles = self._parse_page(response.text)

                # Filter by date
                recent = self.parser.filter_by_date(articles, hours=hours)

                # Remove duplicates
                unique = self.parser.remove_duplicates(recent)

                return unique

        except (httpx.RequestError, Exception) as e:
            raise NewsCollectionError(f"Failed to fetch news: {e}")

    def _parse_page(self, html: str) -> List[Article]:
        """Parse all articles from page HTML"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        article_elements = soup.select('article.post')

        articles = []
        for elem in article_elements:
            try:
                article = self.parser.parse_article(str(elem))
                articles.append(article)
            except Exception as e:
                # Skip malformed articles
                continue

        return articles


class NewsCollectionError(Exception):
    """Exception raised when news collection fails"""
    pass
