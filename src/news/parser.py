"""
TechCrunch AI News Parser
GREEN phase: Minimal implementation to pass tests
"""

import hashlib
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup

from src.models.episode import Article

class TechCrunchParser:
    """Parser for TechCrunch AI news articles"""

    def parse_article(self, html: str) -> Article:
        """Parse a single article from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_elem = soup.select_one('h2.post__title a')
        title = title_elem.text.strip() if title_elem else ""

        # Extract URL
        url_path = title_elem.get('href', '') if title_elem else ""
        url = f"https://techcrunch.com{url_path}" if url_path else ""

        # Extract description
        desc_elem = soup.select_one('.post__content p')
        description = desc_elem.text.strip() if desc_elem else ""

        # Extract publication date
        time_elem = soup.select_one('time')
        datetime_str = time_elem.get('datetime', '') if time_elem else ""
        published_at = (
            datetime.fromisoformat(datetime_str.replace('+00:00', ''))
            if datetime_str else datetime.now()
        )

        # Generate article ID
        article_id = self.generate_article_id(url)

        return Article(
            article_id=article_id,
            title=title,
            description=description,
            url=url,
            published_at=published_at,
            source="techcrunch"
        )

    def filter_by_date(self, articles: List[Article], hours: int = 24) -> List[Article]:
        """Filter articles published within specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            article for article in articles
            if article.published_at > cutoff
        ]

    def remove_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles by URL"""
        seen_urls = set()
        unique = []

        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique.append(article)

        return unique

    def generate_article_id(self, url: str) -> str:
        """Generate consistent article ID from URL using SHA-256"""
        return hashlib.sha256(url.encode()).hexdigest()[:12]
