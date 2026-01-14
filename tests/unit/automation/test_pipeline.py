"""
Unit tests for Episode Pipeline
RED phase: Writing tests first
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date
from src.automation.pipeline import EpisodePipeline, PipelineError
from src.models.episode import Article, Episode


class TestEpisodePipeline:
    """Test episode generation pipeline"""

    @pytest.fixture
    def pipeline(self):
        return EpisodePipeline()

    @pytest.fixture
    def sample_articles(self):
        return [
            Article(
                article_id="1",
                title="GPT-5 Released",
                description="OpenAI releases GPT-5",
                url="https://example.com/1",
                published_at=date.today(),
                source="techcrunch"
            ),
            Article(
                article_id="2",
                title="Google Gemini Update",
                description="New Gemini features",
                url="https://example.com/2",
                published_at=date.today(),
                source="techcrunch"
            ),
        ]

    @pytest.mark.asyncio
    async def test_generate_episode_success(self, pipeline, sample_articles):
        """Test successful episode generation"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = sample_articles
            mock_script.return_value = "Доброе утро! Test script with news."

            episode = await pipeline.generate_episode(date(2026, 1, 14))

            assert episode is not None
            assert episode.episode_id == "ep-2026-01-14"
            assert episode.article_count == 2
            assert episode.script_text == "Доброе утро! Test script with news."
            assert episode.script_word_count == 6

    @pytest.mark.asyncio
    async def test_generate_episode_uses_today_if_no_date(self, pipeline, sample_articles):
        """Test that today's date is used by default"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = sample_articles
            mock_script.return_value = "Доброе утро! Script."

            episode = await pipeline.generate_episode()

            assert episode.date == date.today()
            assert episode.episode_id == f"ep-{date.today().isoformat()}"

    @pytest.mark.asyncio
    async def test_generate_episode_calls_services_in_order(self, pipeline, sample_articles):
        """Test that pipeline stages execute in correct order"""
        call_order = []

        async def mock_collect(*args, **kwargs):
            call_order.append('news')
            return sample_articles

        async def mock_generate(*args, **kwargs):
            call_order.append('script')
            return "Script text"

        with patch.object(pipeline.news_service, 'collect_latest', side_effect=mock_collect), \
             patch.object(pipeline.script_generator, 'generate', side_effect=mock_generate):

            await pipeline.generate_episode()

            assert call_order == ['news', 'script']

    @pytest.mark.asyncio
    async def test_generate_episode_fails_on_no_articles(self, pipeline):
        """Test that pipeline fails when no articles found"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news:
            mock_news.return_value = []

            with pytest.raises(PipelineError, match="No articles found"):
                await pipeline.generate_episode()

    @pytest.mark.asyncio
    async def test_generate_episode_handles_news_service_error(self, pipeline):
        """Test error handling for news collection failure"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news:
            mock_news.side_effect = Exception("News API down")

            with pytest.raises(PipelineError, match="Episode generation failed"):
                await pipeline.generate_episode()

    @pytest.mark.asyncio
    async def test_generate_episode_handles_script_generation_error(self, pipeline, sample_articles):
        """Test error handling for script generation failure"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = sample_articles
            mock_script.side_effect = Exception("LLM API down")

            with pytest.raises(PipelineError, match="Episode generation failed"):
                await pipeline.generate_episode()

    @pytest.mark.asyncio
    async def test_generate_episode_sets_correct_status(self, pipeline, sample_articles):
        """Test that episode status is set correctly"""
        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = sample_articles
            mock_script.return_value = "Script text"

            episode = await pipeline.generate_episode()

            # Since audio_url is None (placeholder), status should be "script_only"
            assert episode.status == "script_only"

    @pytest.mark.asyncio
    async def test_generate_episode_calculates_word_count(self, pipeline, sample_articles):
        """Test that script word count is calculated"""
        script_text = "Доброе утро! " + " ".join(["word"] * 100)

        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = sample_articles
            mock_script.return_value = script_text

            episode = await pipeline.generate_episode()

            assert episode.script_word_count == 102  # "Доброе утро!" + 100 words

    @pytest.mark.asyncio
    async def test_generate_episode_includes_article_count(self, pipeline):
        """Test that article count is tracked"""
        articles = [
            Article(
                article_id=str(i),
                title=f"Article {i}",
                description=f"Description {i}",
                url=f"https://example.com/{i}",
                published_at=date.today(),
                source="techcrunch"
            )
            for i in range(5)
        ]

        with patch.object(pipeline.news_service, 'collect_latest') as mock_news, \
             patch.object(pipeline.script_generator, 'generate') as mock_script:

            mock_news.return_value = articles
            mock_script.return_value = "Script"

            episode = await pipeline.generate_episode()

            assert episode.article_count == 5
