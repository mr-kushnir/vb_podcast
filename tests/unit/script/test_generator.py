"""
Unit tests for Script Generator - LLM Integration
RED phase: Writing tests first
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date
from src.script.generator import ScriptGenerator
from src.models.episode import Article


class TestScriptGenerator:
    """Test LLM-based script generation"""

    @pytest.fixture
    def generator(self):
        return ScriptGenerator()

    @pytest.fixture
    def sample_articles(self):
        return [
            Article(
                article_id="1",
                title="OpenAI releases GPT-5",
                description="New model with enhanced capabilities",
                url="https://example.com/1",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            ),
            Article(
                article_id="2",
                title="Google announces Gemini Pro 2.0",
                description="Multimodal AI breakthrough",
                url="https://example.com/2",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            ),
            Article(
                article_id="3",
                title="Meta unveils new AR glasses",
                description="AI-powered augmented reality",
                url="https://example.com/3",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            ),
        ]

    @pytest.mark.asyncio
    async def test_generate_calls_yagpt_api(self, generator, sample_articles):
        """Test that generate makes API call to YaGPT"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt:
            mock_yagpt.return_value = "Доброе утро! Сегодня 3 новости об ИИ..."

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            assert mock_yagpt.called
            assert "Доброе утро" in result

    @pytest.mark.asyncio
    async def test_generate_includes_all_articles(self, generator, sample_articles):
        """Test that all articles are mentioned in script"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt:
            mock_yagpt.return_value = """Доброе утро!
            OpenAI releases GPT-5. New model with enhanced capabilities.
            Google announces Gemini Pro 2.0. Multimodal AI breakthrough.
            Meta unveils new AR glasses. AI-powered augmented reality.
            """

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            assert "GPT-5" in result
            assert "Gemini Pro" in result
            assert "AR glasses" in result

    @pytest.mark.asyncio
    async def test_generate_controls_duration(self, generator, sample_articles):
        """Test that script length is within target duration (3-5 min = 450-750 words)"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt:
            # Generate script with ~600 words including greeting
            script_words = ["Доброе", "утро!"] + ["слово"] * 598
            mock_yagpt.return_value = " ".join(script_words)

            result = await generator.generate(sample_articles, date(2026, 1, 14))
            word_count = len(result.split())

            assert 450 <= word_count <= 750

    @pytest.mark.asyncio
    async def test_fallback_to_claude_on_yagpt_failure(self, generator, sample_articles):
        """Test fallback to Claude when YaGPT fails"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt, \
             patch.object(generator, '_call_claude') as mock_claude:

            mock_yagpt.side_effect = Exception("YaGPT unavailable")
            mock_claude.return_value = "Доброе утро! (Claude generated)"

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            assert mock_yagpt.called
            assert mock_claude.called
            assert "Доброе утро" in result

    @pytest.mark.asyncio
    async def test_fallback_to_template_on_all_llm_failures(self, generator, sample_articles):
        """Test template fallback when all LLMs fail"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt, \
             patch.object(generator, '_call_claude') as mock_claude:

            mock_yagpt.side_effect = Exception("YaGPT down")
            mock_claude.side_effect = Exception("Claude down")

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            # Should still generate using template
            assert "Доброе утро" in result
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_includes_humor(self, generator, sample_articles):
        """Test that script includes ironic/playful commentary"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt:
            mock_yagpt.return_value = """Доброе утро!
            OpenAI снова удивляет мир новой версией GPT - видимо, они не спят!
            Google не отстает с Gemini Pro 2.0 - конкуренция в самом разгаре.
            """

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            # Check for conversational/humorous elements
            assert any(marker in result for marker in ["!", "видимо", "конечно", "неожиданно"])

    @pytest.mark.asyncio
    async def test_estimate_duration(self, generator):
        """Test duration estimation (150 words/min)"""
        script = " ".join(["word"] * 600)  # 600 words

        duration = generator.estimate_duration_minutes(script)

        assert 3.5 <= duration <= 4.5  # ~4 minutes


class TestContentValidation:
    """Test content validation and safety"""

    @pytest.fixture
    def generator(self):
        return ScriptGenerator()

    @pytest.mark.asyncio
    async def test_validate_script_structure(self, generator):
        """Test that script has required structure"""
        script = """Доброе утро! С вами AI Morning Podcast.

        Новость 1: OpenAI GPT-5
        Description here.

        Новость 2: Google Gemini
        More details.

        Это был обзор новостей. До встречи!"""

        is_valid = generator.validate_structure(script)

        assert is_valid

    @pytest.mark.asyncio
    async def test_reject_inappropriate_content(self, generator):
        """Test content safety filter"""
        inappropriate_script = "Offensive content here [CENSORED]"

        is_safe = generator.is_safe_content(inappropriate_script)

        assert not is_safe

    @pytest.mark.asyncio
    async def test_reject_empty_script(self, generator):
        """Test rejection of empty/invalid scripts"""
        assert not generator.validate_structure("")
        assert not generator.validate_structure("   ")


class TestCircuitBreaker:
    """Test retry and circuit breaker logic"""

    @pytest.fixture
    def generator(self):
        return ScriptGenerator()

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, generator, sample_articles=[]):
        """Test retry on LLM timeout"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt:
            # First call times out, second succeeds
            mock_yagpt.side_effect = [
                Exception("Timeout"),
                "Доброе утро! Script here."
            ]

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            assert mock_yagpt.call_count >= 2

    @pytest.mark.asyncio
    async def test_max_retries_enforced(self, generator, sample_articles=[]):
        """Test that max retries limit is respected"""
        with patch.object(generator, '_call_yagpt') as mock_yagpt, \
             patch.object(generator, '_call_claude') as mock_claude:

            # Both fail repeatedly
            mock_yagpt.side_effect = Exception("Always fails")
            mock_claude.side_effect = Exception("Always fails")

            result = await generator.generate(sample_articles, date(2026, 1, 14))

            # Should fall back to template after max retries
            assert "Доброе утро" in result
            assert mock_yagpt.call_count <= 3  # Max 3 retries


class TestArticleHandling:
    """Test handling different article counts"""

    @pytest.fixture
    def generator(self):
        return ScriptGenerator()

    @pytest.mark.asyncio
    async def test_handle_insufficient_articles(self, generator):
        """Test graceful handling of only 2 articles"""
        articles = [
            Article(
                article_id="1",
                title="News 1",
                description="Description 1",
                url="https://example.com/1",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            ),
            Article(
                article_id="2",
                title="News 2",
                description="Description 2",
                url="https://example.com/2",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            ),
        ]

        result = await generator.generate(articles, date(2026, 1, 14))

        assert len(result) > 0
        # Should acknowledge slow news day
        assert len(result.split()) < 500  # Shorter script

    @pytest.mark.asyncio
    async def test_handle_many_articles(self, generator):
        """Test handling of 10+ articles"""
        articles = [
            Article(
                article_id=str(i),
                title=f"News {i}",
                description=f"Description {i}",
                url=f"https://example.com/{i}",
                published_at=date(2026, 1, 14),
                source="techcrunch"
            )
            for i in range(10)
        ]

        result = await generator.generate(articles, date(2026, 1, 14))

        # Should select top 5-7 articles
        assert len(result) > 0
        word_count = len(result.split())
        assert word_count <= 800  # Don't exceed reasonable length
