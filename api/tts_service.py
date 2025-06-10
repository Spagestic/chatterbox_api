"""
Main TTS service class with all API endpoints.
"""

import io
import base64
import warnings
from typing import Optional

import modal
from fastapi.responses import StreamingResponse, Response
from fastapi import HTTPException, File, UploadFile, Form

from .config import app, image
from .models import TTSRequest, TTSResponse, HealthResponse
from .audio_utils import AudioUtils

with image.imports():
    from chatterbox.tts import ChatterboxTTS
    # Suppress specific transformers deprecation warnings
    warnings.filterwarnings("ignore", message=".*past_key_values.*", category=FutureWarning)


@app.cls(
    gpu="a10g", 
    scaledown_window=60 * 5, 
    enable_memory_snapshot=True
    )
@modal.concurrent(
    max_inputs=10
    )
class ChatterboxTTSService:
    """
    Advanced text-to-speech service using Chatterbox TTS model.
    
    Provides multiple endpoints for different use cases including
    voice cloning, file uploads, and JSON responses.
    """
    
    @modal.enter()
    def load(self):
        """Load the Chatterbox TTS model on container startup."""
        print("Loading Chatterbox TTS model...")
        
        # Suppress transformers deprecation warnings
        warnings.filterwarnings("ignore", message=".*past_key_values.*", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*tuple of tuples.*", category=FutureWarning)
        
        self.model = ChatterboxTTS.from_pretrained(device="cuda")
        print(f"Model loaded successfully! Sample rate: {self.model.sr}")

    def _validate_text_input(self, text: str) -> None:
        """Validate text input parameters."""
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

    def _process_voice_prompt(self, voice_prompt_base64: Optional[str]) -> Optional[str]:
        """Process base64 encoded voice prompt and return temp file path."""
        if not voice_prompt_base64:
            return None
            
        try:
            audio_data = base64.b64decode(voice_prompt_base64)
            return AudioUtils.save_temp_audio_file(audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid voice prompt audio: {str(e)}")

    def _generate_audio(self, text: str, audio_prompt_path: Optional[str] = None):
        """Generate audio with optional voice prompt."""
        print(f"Generating audio for text: {text[:50]}...")
        
        try:
            if audio_prompt_path:
                wav = self.model.generate(text, audio_prompt_path=audio_prompt_path)
                AudioUtils.cleanup_temp_file(audio_prompt_path)
            else:
                wav = self.model.generate(text)
            return wav
        except Exception as e:
            if audio_prompt_path:
                AudioUtils.cleanup_temp_file(audio_prompt_path)
            raise e

    @modal.fastapi_endpoint(docs=True, method="GET")
    def health(self) -> HealthResponse:
        """Health check endpoint to verify model status."""
        return HealthResponse(
            status="healthy", 
            model_loaded=hasattr(self, 'model') and self.model is not None
        )

    @modal.fastapi_endpoint(docs=True, method="POST")
    def generate_audio(self, request: TTSRequest) -> StreamingResponse:
        """
        Generate speech audio from text with optional voice prompt.
        
        Args:
            request: TTSRequest containing text and optional voice prompt
            
        Returns:
            StreamingResponse with generated audio as WAV file
        """
        try:
            self._validate_text_input(request.text)
            audio_prompt_path = self._process_voice_prompt(request.voice_prompt_base64)
            
            # Generate audio
            wav = self._generate_audio(request.text, audio_prompt_path)

            # Create audio buffer
            buffer = AudioUtils.save_audio_to_buffer(wav, self.model.sr)
            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=generated_speech.wav",
                    "X-Audio-Duration": str(len(wav[0]) / self.model.sr)
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    @modal.fastapi_endpoint(docs=True, method="POST")
    def generate_with_file(
        self, 
        text: str = Form(..., description="Text to convert to speech"),
        voice_prompt: Optional[UploadFile] = File(None, description="Optional voice prompt audio file")
    ) -> StreamingResponse:
        """
        Generate speech audio from text with optional voice prompt file upload.
        
        Args:
            text: Text to convert to speech
            voice_prompt: Optional audio file for voice cloning
            
        Returns:
            StreamingResponse with generated audio as WAV file
        """
        try:
            self._validate_text_input(text)
            
            # Handle voice prompt file if provided
            audio_prompt_path = None
            if voice_prompt:
                if voice_prompt.content_type not in ["audio/wav", "audio/mpeg", "audio/mp3"]:
                    raise HTTPException(
                        status_code=400, 
                        detail="Voice prompt must be WAV, MP3, or MPEG audio file"
                    )
                
                # Read and save the uploaded file
                audio_data = voice_prompt.file.read()
                audio_prompt_path = AudioUtils.save_temp_audio_file(audio_data)

            # Generate audio
            wav = self._generate_audio(text, audio_prompt_path)

            # Create audio buffer
            buffer = AudioUtils.save_audio_to_buffer(wav, self.model.sr)
            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=generated_speech.wav",
                    "X-Audio-Duration": str(len(wav[0]) / self.model.sr)
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    @modal.fastapi_endpoint(docs=True, method="POST")
    def generate_json(self, request: TTSRequest) -> TTSResponse:
        """
        Generate speech audio and return as JSON with base64 encoded audio.
        
        Args:
            request: TTSRequest containing text and optional voice prompt
            
        Returns:
            TTSResponse with base64 encoded audio data
        """
        try:
            self._validate_text_input(request.text)
            audio_prompt_path = self._process_voice_prompt(request.voice_prompt_base64)
            
            # Generate audio
            wav = self._generate_audio(request.text, audio_prompt_path)

            # Convert to base64
            buffer = AudioUtils.save_audio_to_buffer(wav, self.model.sr)
            audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            duration = len(wav[0]) / self.model.sr

            return TTSResponse(
                success=True,
                message="Audio generated successfully",
                audio_base64=audio_base64,
                duration_seconds=duration
            )

        except HTTPException as http_exc:
            return TTSResponse(success=False, message=str(http_exc.detail))
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return TTSResponse(success=False, message=f"Audio generation failed: {str(e)}")

    @modal.fastapi_endpoint(docs=True, method="POST")  
    def generate(self, prompt: str):
        """
        Legacy endpoint for backward compatibility.
        Generate audio waveform from the input text.
        """
        try:
            # Generate audio waveform from the input text
            wav = self.model.generate(prompt)

            # Create audio buffer
            buffer = AudioUtils.save_audio_to_buffer(wav, self.model.sr)

            # Return the audio as a streaming response with appropriate MIME type.
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
            )
        except Exception as e:
            print(f"Error in legacy endpoint: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
            
    @modal.fastapi_endpoint(docs=True, method="POST")
    def generate_audio_file(self, request: TTSRequest) -> Response:
        """
        Generate speech audio from text with optional voice prompt and return as a complete file.
        
        Unlike the streaming endpoint, this returns the entire file at once.
        
        Args:
            request: TTSRequest containing text and optional voice prompt
            
        Returns:
            Response with complete audio file data
        """
        try:
            self._validate_text_input(request.text)
            audio_prompt_path = self._process_voice_prompt(request.voice_prompt_base64)
            
            # Generate audio
            wav = self._generate_audio(request.text, audio_prompt_path)

            # Create audio buffer
            buffer = AudioUtils.save_audio_to_buffer(wav, self.model.sr)
            audio_data = buffer.read()
            duration = len(wav[0]) / self.model.sr
            
            # Return the complete audio file
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=generated_speech.wav",
                    "X-Audio-Duration": str(duration)
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
