"""
Podcast Script Generator
Uses LLM (YaGPT/Claude) to generate engaging scripts
"""

from typing import List
from datetime import date

from src.models.episode import Article

class ScriptGenerator:
    """Generate podcast scripts from news articles"""

    async def generate(self, articles: List[Article], target_date: date) -> str:
        """Generate script from articles"""
        # TODO: Implement LLM integration
        # For now, use template-based generation
        return self._template_script(articles, target_date)

    def _template_script(self, articles: List[Article], target_date: date) -> str:
        """Generate script using template (fallback)"""
        date_str = target_date.strftime("%d %B %Y")

        intro = f"""Доброе утро! С вами AI Morning Podcast.

Сегодня, {date_str}, у нас {len(articles)} интересных новостей из мира искусственного интеллекта.

"""

        news_sections = []
        for i, article in enumerate(articles[:7], 1):
            section = f"""Новость {i}: {article.title}

{article.description}

"""
            news_sections.append(section)

        outro = """Это был краткий обзор ключевых AI новостей. Следите за обновлениями, и до встречи завтра!"""

        return intro + "\n".join(news_sections) + outro

    def estimate_duration_minutes(self, script: str) -> float:
        """Estimate reading duration in minutes (150 words/min)"""
        word_count = len(script.split())
        return word_count / 150.0
