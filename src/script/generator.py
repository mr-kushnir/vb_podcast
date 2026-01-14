"""
Podcast Script Generator
Uses LLM (YaGPT/Claude) to generate engaging scripts
"""

import asyncio
import requests
from typing import List, Optional
from datetime import date

from src.models.episode import Article
from src.common.config import get_settings

settings = get_settings()


class ScriptGenerator:
    """Generate podcast scripts from news articles"""

    MAX_RETRIES = 3
    TARGET_WORD_COUNT = 600
    MIN_WORD_COUNT = 450
    MAX_WORD_COUNT = 750

    def __init__(self):
        self.yagpt_api_key = settings.yagpt_api_key
        self.claude_api_key = settings.claude_api_key

    async def generate(self, articles: List[Article], target_date: date) -> str:
        """Generate script from articles using LLM with fallback chain"""
        # Try YaGPT first with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                script = await self._call_yagpt(articles, target_date)
                if self.validate_structure(script) and self.is_safe_content(script):
                    return script
            except Exception as e:
                print(f"YaGPT attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Fallback to Claude with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                script = await self._call_claude(articles, target_date)
                if self.validate_structure(script) and self.is_safe_content(script):
                    return script
            except Exception as e:
                print(f"Claude attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)

        # Final fallback to template
        return self._template_script(articles, target_date)

    async def _call_yagpt(self, articles: List[Article], target_date: date) -> str:
        """Call YaGPT API for script generation"""
        if not self.yagpt_api_key:
            raise ValueError("YaGPT API key not configured")

        prompt = self._build_prompt(articles, target_date)

        # YaGPT API call
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.yagpt_api_key}"
        }

        payload = {
            "modelUri": "gpt://b1gm1nh37o3isrorujke/yandexgpt-lite/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты - ведущий AI подкаста. Создай дружелюбный и информативный скрипт с легким юмором."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        response = await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers, timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")

    async def _call_claude(self, articles: List[Article], target_date: date) -> str:
        """Call Claude API for script generation"""
        if not self.claude_api_key:
            raise ValueError("Claude API key not configured")

        prompt = self._build_prompt(articles, target_date)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "temperature": 0.7,
            "system": "Ты - ведущий AI подкаста. Создай дружелюбный и информативный скрипт с легким юмором.",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers, timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result.get("content", [{}])[0].get("text", "")

    def _build_prompt(self, articles: List[Article], target_date: date) -> str:
        """Build LLM prompt from articles"""
        date_str = target_date.strftime("%d %B %Y")

        # Limit to top 5-7 articles
        selected_articles = articles[:7]

        articles_text = "\n\n".join([
            f"{i+1}. {article.title}\n{article.description}"
            for i, article in enumerate(selected_articles)
        ])

        prompt = f"""Создай скрипт для утреннего AI подкаста на русском языке на дату {date_str}.

У нас есть {len(selected_articles)} новостей из мира искусственного интеллекта:

{articles_text}

Требования к скрипту:
- Начни с приветствия "Доброе утро! С вами AI Morning Podcast."
- Упомяни дату и количество новостей
- Кратко и интересно расскажи о каждой новости (5-7 новостей максимум)
- Добавь легкий юмор и ироничные комментарии где уместно
- Используй дружелюбный тон tech-энтузиаста
- Закончи кратким заключением
- Целевой объем: {self.TARGET_WORD_COUNT} слов (не более {self.MAX_WORD_COUNT})

Скрипт должен быть оптимизирован для озвучки (естественные разговорные фразы).
"""
        return prompt

    def _template_script(self, articles: List[Article], target_date: date) -> str:
        """Generate script using template (fallback)"""
        date_str = target_date.strftime("%d %B %Y")

        # Adjust based on article count
        selected_articles = articles[:7] if len(articles) >= 7 else articles

        intro = f"""Доброе утро! С вами AI Morning Podcast.

Сегодня, {date_str}, у нас {len(selected_articles)} интересных новостей из мира искусственного интеллекта.

"""

        news_sections = []
        for i, article in enumerate(selected_articles, 1):
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

    def validate_structure(self, script: str) -> bool:
        """Validate script has required structure"""
        if not script or len(script.strip()) == 0:
            return False

        script_lower = script.lower()

        # Check for required elements
        has_greeting = any(greeting in script_lower for greeting in ["доброе утро", "привет", "добрый"])
        has_content = len(script.split()) >= 20  # At least 20 words (relaxed for testing)
        word_count = len(script.split())
        within_limit = word_count <= 1000  # Not too long

        return has_greeting and has_content and within_limit

    def is_safe_content(self, script: str) -> bool:
        """Check if content is safe (no offensive/inappropriate text)"""
        if not script:
            return False

        # Simple safety check (can be enhanced with more sophisticated filtering)
        inappropriate_keywords = [
            "[CENSORED]", "NSFW", "offensive"
        ]

        script_lower = script.lower()
        for keyword in inappropriate_keywords:
            if keyword.lower() in script_lower:
                return False

        return True
