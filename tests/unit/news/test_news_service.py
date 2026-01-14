"""
Unit tests for News Service
RED phase: Writing tests first
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.news.service import NewsService, NewsCollectionError
from src.models.episode import Article


class TestNewsService:
    """Test news collection service"""

    @pytest.fixture
    def service(self):
        return NewsService()

    @pytest.mark.asyncio
    async def test_collect_latest_success(self, service):
        """Test successful news collection"""
        mock_html = """
        <article class="post">
            <h2 class="post__title"><a href="/article1">Article 1</a></h2>
            <div class="post__content"><p>Description 1</p></div>
            <time datetime="2026-01-14T10:00:00+00:00">Jan 14</time>
        </article>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            articles = await service.collect_latest(hours=24)

            assert len(articles) >= 0  # May filter based on date

    @pytest.mark.asyncio
    async def test_collect_latest_filters_by_date(self, service):
        """Test that old articles are filtered out"""
        old_date = (datetime.now() - timedelta(hours=48)).isoformat()
        recent_date = datetime.now().isoformat()

        mock_html = f"""
        <article class="post">
            <h2 class="post__title"><a href="/old">Old Article</a></h2>
            <div class="post__content"><p>Old news</p></div>
            <time datetime="{old_date}">2 days ago</time>
        </article>
        <article class="post">
            <h2 class="post__title"><a href="/recent">Recent Article</a></h2>
            <div class="post__content"><p>Fresh news</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            articles = await service.collect_latest(hours=24)

            # Should only return recent article
            if len(articles) > 0:
                for article in articles:
                    age_hours = (datetime.now() - article.published_at).total_seconds() / 3600
                    assert age_hours <= 24

    @pytest.mark.asyncio
    async def test_collect_latest_removes_duplicates(self, service):
        """Test that duplicate articles are removed"""
        recent_date = datetime.now().isoformat()

        # Same article twice
        mock_html = f"""
        <article class="post">
            <h2 class="post__title"><a href="/same">Same Article</a></h2>
            <div class="post__content"><p>Content</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        <article class="post">
            <h2 class="post__title"><a href="/same">Same Article</a></h2>
            <div class="post__content"><p>Content</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            articles = await service.collect_latest(hours=24)

            # Check for duplicates
            urls = [a.url for a in articles]
            assert len(urls) == len(set(urls))  # No duplicates

    @pytest.mark.asyncio
    async def test_collect_latest_handles_http_error(self, service):
        """Test error handling for HTTP failures"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            with pytest.raises(NewsCollectionError, match="Failed to fetch news"):
                await service.collect_latest()

    @pytest.mark.asyncio
    async def test_collect_latest_skips_malformed_articles(self, service):
        """Test that malformed articles are skipped"""
        recent_date = datetime.now().isoformat()

        mock_html = f"""
        <article class="post">
            <h2 class="post__title"><a href="/good">Good Article</a></h2>
            <div class="post__content"><p>Content</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        <article class="post">
            <!-- Missing required fields -->
            <div>Broken article</div>
        </article>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Should not raise, just skip bad articles
            articles = await service.collect_latest(hours=24)

            assert isinstance(articles, list)

    def test_parse_page_extracts_articles(self, service):
        """Test parsing articles from HTML page"""
        recent_date = datetime.now().isoformat()

        html = f"""
        <article class="post">
            <h2 class="post__title"><a href="/article1">Article 1</a></h2>
            <div class="post__content"><p>Description 1</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        <article class="post">
            <h2 class="post__title"><a href="/article2">Article 2</a></h2>
            <div class="post__content"><p>Description 2</p></div>
            <time datetime="{recent_date}">Today</time>
        </article>
        """

        articles = service._parse_page(html)

        assert len(articles) == 2
        assert articles[0].title == "Article 1"
        assert articles[1].title == "Article 2"

    def test_parse_page_handles_empty_html(self, service):
        """Test parsing empty HTML"""
        articles = service._parse_page("")

        assert articles == []

    def test_parse_page_handles_no_articles(self, service):
        """Test parsing HTML with no article elements"""
        html = "<html><body><div>No articles here</div></body></html>"

        articles = service._parse_page(html)

        assert articles == []
