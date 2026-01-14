"""
Application Configuration using Pydantic Settings
Loads from .env file and environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Application
    debug: bool = False
    port: int = 8080
    domain: str = "podcast.rapidapp.ru"

    # YouTrack
    youtrack_url: str
    youtrack_token: str
    youtrack_project: str = "POD"

    # GitHub
    github_token: str
    github_repo: str

    # Yandex Cloud
    yc_token: str
    yc_cloud_id: str
    yc_folder_id: str
    yc_registry_id: str
    yc_service_account_id: str

    # Yandex YDB
    ydb_endpoint: str
    ydb_database: str

    # Yandex S3
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket: str

    # ElevenLabs TTS
    elevenlabs_api_key: str

    # Optional: LLM APIs
    yagpt_api_key: str = ""
    claude_api_key: str = ""

    # Optional: Additional Yandex Cloud fields
    yc_sa_key_file: str = ""
    yandex_domain: str = ""
    bot_token: str = ""
    port_env: int = 8080  # Alternative port from env

    # Automation
    auto_commit: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
