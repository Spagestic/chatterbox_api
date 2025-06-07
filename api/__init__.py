
"""
Chatterbox TTS API package.

This package provides a modular text-to-speech API using the Chatterbox TTS model
deployed on Modal with GPU acceleration.
"""

from .config import app, image
from .models import TTSRequest, TTSResponse, HealthResponse
from .audio_utils import AudioUtils
from .tts_service import ChatterboxTTSService

__all__ = [
    "app",
    "image", 
    "TTSRequest",
    "TTSResponse",
    "HealthResponse",
    "AudioUtils",
    "ChatterboxTTSService"
]
