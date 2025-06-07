
"""
Pydantic models for request/response validation and API documentation.
"""

from typing import Optional
from pydantic import BaseModel


class TTSRequest(BaseModel):
    """Request model for TTS generation with optional voice cloning."""
    text: str
    voice_prompt_base64: Optional[str] = None  # Base64 encoded audio file
    

class TTSResponse(BaseModel):
    """Response model for TTS generation with JSON output."""
    success: bool
    message: str
    audio_base64: Optional[str] = None  # Base64 encoded audio response
    duration_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    model_loaded: bool
