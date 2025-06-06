# ---
# output-directory: "/tmp/chatterbox-tts"
# lambda-test: false
# cmd: ["modal", "serve", "06_gpu_and_ml/test-to-audio/chatterbox_tts.py"]
# ---


# # Enhanced Chatterbox TTS API on Modal

# This example demonstrates how to deploy an advanced text-to-speech (TTS) API using the Chatterbox TTS model on Modal.
# The API provides multiple endpoints for different use cases including voice cloning, file uploads, and JSON responses.
# 
# Key Features:
# - Multiple API endpoints (streaming, JSON, file upload)
# - Voice cloning with custom audio prompts
# - Comprehensive error handling and validation
# - Health monitoring endpoint
# - Request/response models with Pydantic
# - Backward compatibility with legacy endpoints
# - Enhanced documentation and examples
#
# We use Modal's class-based approach with GPU acceleration to provide fast, scalable TTS inference.

# ## Setup

# Import the necessary modules for Modal deployment and TTS functionality.

import io
import base64
from typing import Optional, Union
from pathlib import Path

import modal
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, File, UploadFile, Form

# ## Define a container image

# We start with Modal's baseline `debian_slim` image and install the required packages.
# - `chatterbox-tts`: The TTS model library
# - `fastapi`: Web framework for creating the API endpoint
# - `pydantic`: For request/response models

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "chatterbox-tts==0.1.1", "fastapi[standard]", "pydantic", "numpy"
)
app = modal.App("chatterbox-api-example", image=image)

# Import the required libraries within the image context to ensure they're available
# when the container runs. This includes audio processing and the TTS model itself.

with image.imports():
    import torchaudio as ta
    import numpy as np
    from chatterbox.tts import ChatterboxTTS
    from fastapi import HTTPException, File, UploadFile, Form
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import tempfile
    import os


# ## Request/Response Models

# Define Pydantic models for better API documentation and validation

class TTSRequest(BaseModel):
    text: str
    voice_prompt_base64: Optional[str] = None  # Base64 encoded audio file
    
class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_base64: Optional[str] = None  # Base64 encoded audio response
    duration_seconds: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

# ## The TTS model class

# The TTS service is implemented using Modal's class syntax with GPU acceleration.
# We configure the class to use an A10G GPU with additional parameters:
# #
# - `scaledown_window=60 * 5`: Keep containers alive for 5 minutes after last request
# - `enable_memory_snapshot=True`: Enable [memory snapshots](https://modal.com/docs/guide/memory-snapshot) to optimize cold boot times
# - `@modal.concurrent(max_inputs=10)`: Allow up to 10 concurrent requests per container


@app.cls(gpu="a10g", scaledown_window=60 * 5, enable_memory_snapshot=True)
@modal.concurrent(max_inputs=10)
class Chatterbox:
    @modal.enter()
    def load(self):
        """Load the Chatterbox TTS model on container startup."""
        print("Loading Chatterbox TTS model...")
        self.model = ChatterboxTTS.from_pretrained(device="cuda")
        print(f"Model loaded successfully! Sample rate: {self.model.sr}")

    def _save_audio_to_buffer(self, wav_tensor) -> io.BytesIO:
        """Helper method to save audio tensor to BytesIO buffer."""
        buffer = io.BytesIO()
        ta.save(buffer, wav_tensor, self.model.sr, format="wav")
        buffer.seek(0)
        return buffer

    def _save_temp_audio_file(self, audio_data: bytes) -> str:
        """Save uploaded audio data to a temporary file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            return temp_file.name

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
            if not request.text or len(request.text.strip()) == 0:
                raise HTTPException(status_code=400, detail="Text cannot be empty")
            
            if len(request.text) > 1000:
                raise HTTPException(status_code=400, detail="Text too long (max 1000 characters)")

            # Handle voice prompt if provided
            audio_prompt_path = None
            if request.voice_prompt_base64:
                try:
                    # Decode base64 audio
                    audio_data = base64.b64decode(request.voice_prompt_base64)
                    audio_prompt_path = self._save_temp_audio_file(audio_data)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid voice prompt audio: {str(e)}")

            # Generate audio
            print(f"Generating audio for text: {request.text[:50]}...")
            if audio_prompt_path:
                wav = self.model.generate(request.text, audio_prompt_path=audio_prompt_path)
                # Clean up temporary file
                os.unlink(audio_prompt_path)
            else:
                wav = self.model.generate(request.text)

            # Create audio buffer
            buffer = self._save_audio_to_buffer(wav)
            
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
            if not text or len(text.strip()) == 0:
                raise HTTPException(status_code=400, detail="Text cannot be empty")
            
            if len(text) > 1000:
                raise HTTPException(status_code=400, detail="Text too long (max 1000 characters)")

            # Handle voice prompt file if provided
            audio_prompt_path = None
            if voice_prompt:
                if voice_prompt.content_type not in ["audio/wav", "audio/mpeg", "audio/mp3"]:
                    raise HTTPException(status_code=400, detail="Voice prompt must be WAV, MP3, or MPEG audio file")
                
                # Read and save the uploaded file
                audio_data = voice_prompt.file.read()
                audio_prompt_path = self._save_temp_audio_file(audio_data)

            # Generate audio
            print(f"Generating audio for text: {text[:50]}...")
            if audio_prompt_path:
                wav = self.model.generate(text, audio_prompt_path=audio_prompt_path)
                # Clean up temporary file
                os.unlink(audio_prompt_path)
            else:
                wav = self.model.generate(text)

            # Create audio buffer
            buffer = self._save_audio_to_buffer(wav)
            
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
            if not request.text or len(request.text.strip()) == 0:
                return TTSResponse(success=False, message="Text cannot be empty")
            
            if len(request.text) > 1000:
                return TTSResponse(success=False, message="Text too long (max 1000 characters)")

            # Handle voice prompt if provided
            audio_prompt_path = None
            if request.voice_prompt_base64:
                try:
                    audio_data = base64.b64decode(request.voice_prompt_base64)
                    audio_prompt_path = self._save_temp_audio_file(audio_data)
                except Exception as e:
                    return TTSResponse(success=False, message=f"Invalid voice prompt audio: {str(e)}")

            # Generate audio
            print(f"Generating audio for text: {request.text[:50]}...")
            if audio_prompt_path:
                wav = self.model.generate(request.text, audio_prompt_path=audio_prompt_path)
                os.unlink(audio_prompt_path)
            else:
                wav = self.model.generate(request.text)

            # Convert to base64
            buffer = self._save_audio_to_buffer(wav)
            audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            duration = len(wav[0]) / self.model.sr

            return TTSResponse(
                success=True,
                message="Audio generated successfully",
                audio_base64=audio_base64,
                duration_seconds=duration
            )

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
            buffer = self._save_audio_to_buffer(wav)

            # Return the audio as a streaming response with appropriate MIME type.
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
            )
        except Exception as e:
            print(f"Error in legacy endpoint: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


# ## Deployment and Usage

# Deploy the enhanced Chatterbox API with:
#
# ```shell
# modal deploy chatterbox_tts.py
# ```
#
# ## API Endpoints
#
# The API now provides multiple endpoints for different use cases:
#
# ### 1. Health Check
# ```shell
# curl -X GET "<YOUR-ENDPOINT-URL>/health"
# ```
#
# ### 2. Generate Audio (File Response)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_audio" \
#   -H "Content-Type: application/json" \
#   -d '{"text": "Hello, this is Chatterbox TTS running on Modal!"}' \
#   --output output.wav
# ```
#
# ### 3. Generate Audio with Voice Prompt (File Upload)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_with_file" \
#   -F "text=Hello, this is voice cloning with Chatterbox!" \
#   -F "voice_prompt=@your_voice_sample.wav" \
#   --output cloned_voice.wav
# ```
#
# ### 4. Generate Audio (JSON Response with Base64)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_json" \
#   -H "Content-Type: application/json" \
#   -d '{"text": "This returns JSON with base64 audio data"}' \
#   | jq -r '.audio_base64' | base64 -d > output.wav
# ```
#
# ### 5. Legacy Endpoint (Backward Compatibility)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate" \
#   --data-urlencode "prompt=Legacy endpoint still works!" \
#   --output legacy_output.wav
# ```
#
# ## Python Client Example
#
# ```python
# import requests
# import base64
# import json
#
# # Basic text-to-speech
# response = requests.post(
#     "YOUR-ENDPOINT-URL/generate_audio",
#     json={"text": "Hello from Python!"}
# )
# with open("python_output.wav", "wb") as f:
#     f.write(response.content)
#
# # With voice prompt (base64 encoded)
# with open("voice_sample.wav", "rb") as f:
#     voice_data = base64.b64encode(f.read()).decode()
#
# response = requests.post(
#     "YOUR-ENDPOINT-URL/generate_audio", 
#     json={
#         "text": "This will sound like the provided voice sample!",
#         "voice_prompt_base64": voice_data
#     }
# )
# with open("cloned_output.wav", "wb") as f:
#     f.write(response.content)
# ```
#
# ## Features
#
# - **Multiple Endpoints**: Choose between file streaming, JSON responses, or file uploads
# - **Voice Cloning**: Upload audio samples to clone voices using the voice prompt feature
# - **Error Handling**: Comprehensive error messages and status codes
# - **Health Monitoring**: Health check endpoint for monitoring deployments
# - **Request Validation**: Input validation with clear error messages
# - **Backward Compatibility**: Legacy endpoint still supported
# - **Enhanced Documentation**: OpenAPI/Swagger docs available at `/docs`
#
# ## Performance
#
# This enhanced app maintains the same performance characteristics:
# - ~30 seconds cold boot time (model loading)
# - 2-3 seconds to generate a 5-second audio clip
# - Up to 10 concurrent requests per container
# - 5-minute scale-down window for cost efficiency
# - Memory snapshots enabled for faster cold starts
