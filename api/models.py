
"""
Pydantic models for request/response validation and API documentation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request model for TTS generation with optional voice cloning."""
    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    voice_prompt_base64: Optional[str] = Field(None, description="Base64 encoded voice prompt audio")


class FullTextTTSRequest(BaseModel):
    """Request model for full-text TTS generation with server-side processing."""
    text: str = Field(..., description="Full text to convert to speech (any length)")
    voice_prompt_base64: Optional[str] = Field(None, description="Base64 encoded voice prompt audio")
    max_chunk_size: Optional[int] = Field(800, description="Maximum characters per chunk")
    silence_duration: Optional[float] = Field(0.5, description="Silence duration between chunks (seconds)")
    fade_duration: Optional[float] = Field(0.1, description="Fade in/out duration (seconds)")
    overlap_sentences: Optional[int] = Field(0, description="Number of sentences to overlap between chunks")
    

class TTSResponse(BaseModel):
    """Response model for TTS generation with JSON output."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Status message")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    duration_seconds: Optional[float] = Field(None, description="Duration of generated audio in seconds")


class FullTextTTSResponse(BaseModel):
    """Response model for full-text TTS generation."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Status message")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    duration_seconds: Optional[float] = Field(None, description="Duration of generated audio in seconds")
    processing_info: Optional[dict] = Field(None, description="Information about the processing (chunks, etc.)")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the TTS model is loaded")
