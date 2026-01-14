"""
Episode Generation Pipeline
Orchestrates news → script → audio → publish workflow
"""

import logging
from datetime import date
from typing import Optional

from src.news.service import NewsService
from src.script.generator import ScriptGenerator
from src.audio.tts import TTSService
from src.models.episode import Episode, PipelineState

logger = logging.getLogger(__name__)

class EpisodePipeline:
    """Main pipeline for generating daily episodes"""

    def __init__(self):
        self.news_service = NewsService()
        self.script_generator = ScriptGenerator()
        self.tts_service = TTSService()

    async def generate_episode(self, target_date: Optional[date] = None) -> Episode:
        """Generate complete episode for given date"""
        if target_date is None:
            target_date = date.today()

        episode_id = f"ep-{target_date.isoformat()}"
        logger.info(f"Starting episode generation: {episode_id}")

        try:
            # Stage 1: Collect news
            logger.info("Stage 1: Collecting news...")
            articles = await self.news_service.collect_latest(hours=24)
            logger.info(f"Collected {len(articles)} articles")

            if len(articles) == 0:
                raise PipelineError("No articles found")

            # Stage 2: Generate script
            logger.info("Stage 2: Generating script...")
            script = await self.script_generator.generate(articles, target_date)
            word_count = len(script.split())
            logger.info(f"Generated script: {word_count} words")

            # Stage 3: Generate audio (placeholder)
            logger.info("Stage 3: Audio generation (skipped for demo)")
            audio_url = None  # Would be from TTS service

            # Stage 4: Create episode record
            episode = Episode(
                episode_id=episode_id,
                date=target_date,
                status="completed" if audio_url else "script_only",
                article_count=len(articles),
                script_text=script,
                script_word_count=word_count,
                audio_url=audio_url
            )

            logger.info(f"Episode {episode_id} generation complete!")
            return episode

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise PipelineError(f"Episode generation failed: {e}")


class PipelineError(Exception):
    """Pipeline execution error"""
    pass
