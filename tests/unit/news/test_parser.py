"""
Unit tests for news parser (TechCrunch AI)
RED phase: Writing failing tests first
"""

import pytest
from datetime import datetime, timedelta
from src.news.parser import TechCrunchParser, Article

class TestTechCrunchParser:
    """Test suite for TechCrunch AI news parser"""

    @pytest.fixture
    def parser(self):
        return TechCrunchParser()

    @pytest.mark.asyncio
    async def test_parse_article_from_html(self, parser):
        """Test parsing a single article from HTML"""
        html = """
        <article class="post">
            <h2 class="post__title">
                <a href="/2026/01/14/test-article/">Test AI Article</a>
            </h2>
            <div class="post__content">
                <p>This is a test article about AI.</p>
            </div>
            <time datetime="2026-01-14T10:00:00+00:00">January 14, 2026</time>
        </article>
        """

        article = parser.parse_article(html)

        assert article.title == "Test AI Article"
        assert "test article about AI" in article.description
        assert article.url == "https://techcrunch.com/2026/01/14/test-article/"
        assert article.source == "techcrunch"

    @pytest.mark.asyncio
    async def test_filter_articles_by_24_hours(self, parser):
        """Test filtering articles within 24 hour window"""
        now = datetime.now()
        articles = [
            Article(
                article_id="1",
                title="Recent",
                description="",
                url="",
                published_at=now - timedelta(hours=12),
                source="techcrunch"
            ),
            Article(
                article_id="2",
                title="Old",
                description="",
                url="",
                published_at=now - timedelta(hours=30),
                source="techcrunch"
            )
        ]

        filtered = parser.filter_by_date(articles, hours=24)

        assert len(filtered) == 1
        assert filtered[0].title == "Recent"

    @pytest.mark.asyncio
    async def test_remove_duplicate_articles(self, parser):
        """Test removing duplicate articles by URL"""
        articles = [
            Article(
                article_id="1",
                title="Article 1",
                description="",
                url="https://example.com/article",
                published_at=datetime.now(),
                source="techcrunch"
            ),
            Article(
                article_id="2",
                title="Article 1 Duplicate",
                description="",
                url="https://example.com/article",  # Same URL
                published_at=datetime.now(),
                source="techcrunch"
            ),
            Article(
                article_id="3",
                title="Article 2",
                description="",
                url="https://example.com/article2",
                published_at=datetime.now(),
                source="techcrunch"
            )
        ]

        unique = parser.remove_duplicates(articles)

        assert len(unique) == 2
        assert unique[0].article_id == "1"
        assert unique[1].article_id == "3"

    @pytest.mark.asyncio
    async def test_handle_missing_description(self, parser):
        """Test handling articles without description"""
        html = """
        <article class="post">
            <h2 class="post__title">
                <a href="/article/">Article Without Description</a>
            </h2>
            <time datetime="2026-01-14T10:00:00+00:00">January 14, 2026</time>
        </article>
        """

        article = parser.parse_article(html)

        assert article.title == "Article Without Description"
        assert article.description == ""  # Should use empty string, not None

    @pytest.mark.asyncio
    async def test_generate_article_id(self, parser):
        """Test consistent article ID generation"""
        url = "https://techcrunch.com/2026/01/14/test-article/"

        article_id = parser.generate_article_id(url)

        assert article_id is not None
        assert len(article_id) > 0
        # Same URL should generate same ID
        assert parser.generate_article_id(url) == article_id
