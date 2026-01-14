# Design Patterns - AI Podcast Portal

## Overview

This document describes the key design patterns used in the AI Morning Podcast Portal architecture.

## 1. Repository Pattern

**Purpose**: Abstract data access logic from business logic

**Implementation**:

```python
# src/common/repository.py
from abc import ABC, abstractmethod
from typing import List, Optional

class EpisodeRepository(ABC):
    @abstractmethod
    async def create(self, episode: Episode) -> Episode:
        pass

    @abstractmethod
    async def get_by_id(self, episode_id: str) -> Optional[Episode]:
        pass

    @abstractmethod
    async def get_by_date(self, date: date) -> Optional[Episode]:
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 10) -> List[Episode]:
        pass

    @abstractmethod
    async def update(self, episode: Episode) -> Episode:
        pass

# src/db/ydb_repository.py
class YDBEpisodeRepository(EpisodeRepository):
    def __init__(self, db_client: YDBClient):
        self.db = db_client

    async def create(self, episode: Episode) -> Episode:
        query = "INSERT INTO episodes (...) VALUES (...)"
        await self.db.execute(query, episode.dict())
        return episode

    # ... implement other methods
```

**Benefits**:
- Easy to test (mock repository)
- Can switch databases without changing business logic
- Clear separation of concerns

## 2. Dependency Injection

**Purpose**: Manage dependencies and enable testability

**Implementation using FastAPI**:

```python
# src/common/dependencies.py
from fastapi import Depends

def get_news_service() -> NewsService:
    repo = get_news_repository()
    cache = get_cache_service()
    return NewsService(repository=repo, cache=cache)

def get_episode_repository() -> EpisodeRepository:
    db = get_db_client()
    return YDBEpisodeRepository(db)

# src/news/api.py
@app.get("/api/news")
async def get_news(
    service: NewsService = Depends(get_news_service)
):
    return await service.collect_latest()
```

**Benefits**:
- Easy to swap implementations
- Testable (inject mocks)
- Clear dependency graph

## 3. Circuit Breaker

**Purpose**: Prevent cascading failures from external API calls

**Implementation**:

```python
# src/common/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject immediately
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self):
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)
        )

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
news_circuit = CircuitBreaker(failure_threshold=3, timeout=300)

async def fetch_news_with_circuit():
    return await news_circuit.call(fetch_news_from_techcrunch)
```

**Benefits**:
- Prevents repeated calls to failing services
- Gives services time to recover
- Reduces wasted resources

## 4. Retry with Exponential Backoff

**Purpose**: Handle transient failures gracefully

**Implementation**:

```python
# Using tenacity library
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.RequestError)
)
async def fetch_with_retry(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
```

**Retry schedule**:
- Attempt 1: immediate
- Attempt 2: wait 1 second
- Attempt 3: wait 2 seconds
- Attempt 4: wait 4 seconds (if max attempts > 3)

## 5. Strategy Pattern (Fallback Chain)

**Purpose**: Try multiple strategies until one succeeds

**Implementation**:

```python
# src/script/generator.py
from abc import ABC, abstractmethod

class ScriptGenerationStrategy(ABC):
    @abstractmethod
    async def generate(self, news: List[Article]) -> str:
        pass

class LLMScriptStrategy(ScriptGenerationStrategy):
    async def generate(self, news: List[Article]) -> str:
        # Call YaGPT/Claude API
        pass

class TemplateScriptStrategy(ScriptGenerationStrategy):
    async def generate(self, news: List[Article]) -> str:
        # Use template with basic formatting
        pass

class ScriptGenerator:
    def __init__(self):
        self.strategies = [
            LLMScriptStrategy(),
            TemplateScriptStrategy()  # Fallback
        ]

    async def generate(self, news: List[Article]) -> str:
        for strategy in self.strategies:
            try:
                return await strategy.generate(news)
            except Exception as e:
                logger.warning(f"{strategy.__class__.__name__} failed: {e}")
                continue
        raise AllStrategiesFailedError("All script generation strategies failed")
```

**Benefits**:
- Graceful degradation
- Easy to add new strategies
- Clear fallback chain

## 6. Observer Pattern (Event-Driven Notifications)

**Purpose**: Decouple components, enable extensibility

**Implementation**:

```python
# src/common/events.py
from typing import Callable, List
from dataclasses import dataclass

@dataclass
class EpisodePublishedEvent:
    episode_id: str
    date: str
    audio_url: str

class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type: type, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                await handler(event)

# Usage
event_bus = EventBus()

async def send_telegram_notification(event: EpisodePublishedEvent):
    await telegram_bot.send(f"New episode: {event.audio_url}")

async def update_rss_feed(event: EpisodePublishedEvent):
    await rss_generator.add_episode(event.episode_id)

event_bus.subscribe(EpisodePublishedEvent, send_telegram_notification)
event_bus.subscribe(EpisodePublishedEvent, update_rss_feed)

# In pipeline
await event_bus.publish(EpisodePublishedEvent(...))
```

**Benefits**:
- Loose coupling
- Easy to add new listeners
- Clear event flow

## 7. Builder Pattern (Episode Construction)

**Purpose**: Construct complex objects step by step

**Implementation**:

```python
# src/automation/episode_builder.py
class EpisodeBuilder:
    def __init__(self):
        self._episode = Episode()

    def with_news(self, news: List[Article]):
        self._episode.news = news
        self._episode.article_count = len(news)
        return self

    def with_script(self, script: str):
        self._episode.script_text = script
        self._episode.script_word_count = len(script.split())
        return self

    def with_audio(self, audio_url: str, duration: int, file_size: int):
        self._episode.audio_url = audio_url
        self._episode.audio_duration_seconds = duration
        self._episode.audio_file_size_bytes = file_size
        return self

    def build(self) -> Episode:
        self._episode.validate()
        return self._episode

# Usage
episode = (EpisodeBuilder()
    .with_news(news_articles)
    .with_script(generated_script)
    .with_audio(s3_url, duration, size)
    .build())
```

**Benefits**:
- Clear construction steps
- Validates at the end
- Immutable final object

## 8. Adapter Pattern (External APIs)

**Purpose**: Wrap external APIs with consistent interface

**Implementation**:

```python
# src/common/tts_adapter.py
from abc import ABC, abstractmethod

class TTSAdapter(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass

class ElevenLabsAdapter(TTSAdapter):
    async def synthesize(self, text: str) -> bytes:
        # Call ElevenLabs API
        pass

class YandexSpeechKitAdapter(TTSAdapter):
    async def synthesize(self, text: str) -> bytes:
        # Call Yandex SpeechKit API
        pass

class LocalGTTSAdapter(TTSAdapter):
    async def synthesize(self, text: str) -> bytes:
        # Use gTTS library
        pass

# Factory
def get_tts_adapter(provider: str = "elevenlabs") -> TTSAdapter:
    if provider == "elevenlabs":
        return ElevenLabsAdapter()
    elif provider == "yandex":
        return YandexSpeechKitAdapter()
    elif provider == "gtts":
        return LocalGTTSAdapter()
    raise ValueError(f"Unknown TTS provider: {provider}")
```

**Benefits**:
- Easy to switch providers
- Consistent interface
- Provider-specific logic encapsulated

## 9. Singleton (Configuration)

**Purpose**: Single source of truth for configuration

**Implementation**:

```python
# src/common/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # YouTrack
    youtrack_url: str
    youtrack_token: str

    # APIs
    elevenlabs_api_key: str
    yagpt_api_key: str

    # Storage
    ydb_endpoint: str
    ydb_database: str
    s3_bucket: str

    # App
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Usage
settings = get_settings()
```

**Benefits**:
- Lazy loading
- Type-safe configuration
- Environment variables support

## 10. Facade Pattern (Pipeline Orchestration)

**Purpose**: Simplify complex subsystem interactions

**Implementation**:

```python
# src/automation/pipeline_facade.py
class EpisodePipelineFacade:
    def __init__(
        self,
        news_service: NewsService,
        script_service: ScriptService,
        audio_service: AudioService,
        storage_service: StorageService,
        repository: EpisodeRepository
    ):
        self.news = news_service
        self.script = script_service
        self.audio = audio_service
        self.storage = storage_service
        self.repository = repository

    async def generate_episode(self, date: str) -> Episode:
        """Single method to orchestrate entire pipeline"""
        # Step 1: Collect news
        news = await self.news.collect_latest()

        # Step 2: Generate script
        script = await self.script.generate(news)

        # Step 3: Generate audio
        audio_bytes = await self.audio.synthesize(script)

        # Step 4: Upload to storage
        audio_url = await self.storage.upload(audio_bytes, f"{date}.mp3")

        # Step 5: Save episode
        episode = (EpisodeBuilder()
            .with_news(news)
            .with_script(script)
            .with_audio(audio_url, ...)
            .build())

        await self.repository.create(episode)
        return episode
```

**Benefits**:
- Simple interface for complex operations
- Hides subsystem complexity
- Single entry point for pipeline

## Summary

These patterns work together to create a maintainable, testable, resilient system:

- **Repository** + **DI**: Clean architecture
- **Circuit Breaker** + **Retry**: Resilience
- **Strategy** + **Adapter**: Flexibility
- **Builder** + **Facade**: Simplicity
- **Observer**: Extensibility

All patterns are implemented with async/await for optimal performance.
