"""
Text-to-Speech Service
Integrates with ElevenLabs API
"""

import asyncio
import requests
from typing import Optional
from src.common.config import get_settings

settings = get_settings()


class TTSService:
    """Text-to-Speech audio generation"""

    # ElevenLabs API configuration
    API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    RUSSIAN_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (multilingual)
    MAX_TEXT_LENGTH = 5000
    MAX_RETRIES = 3

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key

    async def synthesize(self, text: str) -> bytes:
        """Generate audio from text using ElevenLabs API"""
        # Validate input
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")

        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {self.MAX_TEXT_LENGTH} characters)")

        # Make API request with retry logic
        return await self._synthesize_with_retry(text)

    async def _synthesize_with_retry(self, text: str, attempt: int = 0) -> bytes:
        """Execute synthesis with exponential backoff retry"""
        try:
            return await self._make_api_call(text)
        except (requests.exceptions.RequestException, Exception) as e:
            # Check if we should retry
            error_msg = str(e)
            is_503 = "503" in error_msg or "Service unavailable" in error_msg

            if is_503 and attempt < self.MAX_RETRIES - 1:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** attempt
                await asyncio.sleep(delay)
                return await self._synthesize_with_retry(text, attempt + 1)
            elif attempt >= self.MAX_RETRIES - 1:
                raise Exception(f"Max retries exceeded: {error_msg}")
            else:
                raise

    async def _make_api_call(self, text: str) -> bytes:
        """Make the actual API call to ElevenLabs"""
        url = f"{self.API_URL}/{self.RUSSIAN_VOICE_ID}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }

        # Make synchronous request (will run in executor)
        response = await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers, timeout=30
        )

        # Handle specific error codes
        if response.status_code == 429:
            quota_reset = response.headers.get('X-RateLimit-Reset', 'unknown')
            raise Exception(f"Quota exceeded. Reset at: {quota_reset}")

        if response.status_code == 503:
            raise requests.exceptions.RequestException(f"Service unavailable: {response.status_code}")

        response.raise_for_status()
        return response.content

    def check_quota(self) -> bool:
        """Check if API quota is available (placeholder)"""
        return True

    async def save_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Save audio to file and upload to S3"""
        from src.storage.s3_client import get_storage

        storage = get_storage()
        audio_path = f"audio/{filename}"

        # Save locally first
        local_path = f"data/audio/{filename}"
        with open(local_path, 'wb') as f:
            f.write(audio_bytes)

        # Upload to S3
        url = await storage.upload_file(local_path, audio_path)
        return url
