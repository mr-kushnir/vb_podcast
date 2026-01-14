"""
Episode domain model
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Article(BaseModel):
    """News article model"""
    article_id: str
    title: str
    description: str
    url: str
    published_at: datetime
    source: str = "techcrunch"

class Episode(BaseModel):
    """Podcast episode model"""
    episode_id: str
    date: date
    status: str = "pending"  # pending|processing|completed|failed
    article_count: int = 0
    script_text: Optional[str] = None
    script_word_count: Optional[int] = None
    audio_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    audio_file_size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None

    def validate_complete(self) -> bool:
        """Check if episode is complete and ready for publication"""
        return all([
            self.script_text,
            self.audio_url,
            self.article_count > 0
        ])

class PipelineState(BaseModel):
    """Pipeline stage execution state"""
    episode_id: str
    stage: str  # news|script|audio|upload
    status: str  # pending|running|completed|failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
