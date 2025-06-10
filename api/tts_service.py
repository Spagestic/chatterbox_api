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
from .models import TTSRequest, TTSResponse, HealthResponse, FullTextTTSRequest, FullTextTTSResponse
from .audio_utils import AudioUtils
from .text_processing import TextChunker
from .audio_concatenator import AudioConcatenator

with image.imports():
    from chatterbox.tts import ChatterboxTTS
    import torch # Add torch import here
    # Suppress specific transformers deprecation warnings
    warnings.filterwarnings("ignore", message=".*past_key_values.*", category=FutureWarning)


@app.cls(
    gpu="a10g", 
    scaledown_window=60 * 60, 
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

    @modal.fastapi_endpoint(docs=True, method="POST")
    def generate_full_text_audio(self, request: FullTextTTSRequest) -> StreamingResponse:
        """
        Generate speech audio from full text with server-side chunking and parallel processing.
        
        This endpoint handles texts of any length by:
        1. Chunking the text intelligently (respecting sentence/paragraph boundaries)
        2. Processing chunks in parallel using GPU resources
        3. Concatenating audio chunks with proper transitions
        4. Returning the final audio file
        
        Args:
            request: FullTextTTSRequest containing text and processing parameters
            
        Returns:
            StreamingResponse with final concatenated audio as WAV file
        """
        try:
            self._validate_text_input(request.text)
            audio_prompt_path = self._process_voice_prompt(request.voice_prompt_base64)
            
            print(f"Processing full text ({len(request.text)} chars) with server-side chunking...")
            
            # Initialize text chunker with request parameters
            chunker = TextChunker(
                max_chunk_size=request.max_chunk_size,
                overlap_sentences=request.overlap_sentences
            )
            
            # Chunk the text
            text_chunks = chunker.chunk_text(request.text)
            chunk_info = chunker.get_chunk_info(text_chunks)
            print(f"Split text into {len(text_chunks)} chunks for processing")
            
            # Initialize audio_chunks variable for processing info
            audio_chunks = []
              # If only one chunk, process directly
            if len(text_chunks) == 1:
                wav = self._generate_audio(text_chunks[0], audio_prompt_path)
                # For single chunk, pass the full wav object to maintain consistency
                final_audio = wav
                audio_chunks = [wav]  # For consistent processing info
            else:
                # Process chunks in parallel
                import concurrent.futures
                import numpy as np
                
                def process_chunk(chunk_text: str):
                    """Process a single chunk."""
                    wav_result = self._generate_audio(chunk_text, audio_prompt_path)
                    # Return the full wav result, not just wav[0]
                    return wav_result
                
                # Use ThreadPoolExecutor for parallel processing
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit all chunks for processing
                    future_to_chunk = {
                        executor.submit(process_chunk, chunk): i 
                        for i, chunk in enumerate(text_chunks)
                    }
                    
                    # Collect results in order
                    results = [None] * len(text_chunks)
                    for future in concurrent.futures.as_completed(future_to_chunk):
                        chunk_index = future_to_chunk[future]
                        try:
                            audio_result = future.result()
                            results[chunk_index] = audio_result
                        except Exception as exc:
                            print(f'Chunk {chunk_index} generated an exception: {exc}')
                            raise HTTPException(status_code=500, detail=f"Failed to process chunk {chunk_index}: {str(exc)}")
                
                # Filter out None results
                audio_chunks = [result for result in results if result is not None]
                
                if len(audio_chunks) != len(text_chunks):
                    raise HTTPException(status_code=500, detail=f"Only {len(audio_chunks)} out of {len(text_chunks)} chunks processed successfully")
                
                # Concatenate audio chunks
                print("Concatenating audio chunks...")
                concatenator = AudioConcatenator(
                    silence_duration=request.silence_duration,
                    fade_duration=request.fade_duration
                )
                
                final_audio = concatenator.concatenate_audio_chunks(audio_chunks, self.model.sr)
            
            # --- Start of new audio processing logic ---
            import torch
            import numpy as np

            processed_tensor = final_audio
            # Unwrap if it's a single-element tuple repeatedly
            while isinstance(processed_tensor, tuple) and len(processed_tensor) == 1:
                processed_tensor = processed_tensor[0]

            # Convert to PyTorch tensor if it's a NumPy array
            if isinstance(processed_tensor, np.ndarray):
                processed_tensor = torch.from_numpy(processed_tensor.astype(np.float32))

            if not isinstance(processed_tensor, torch.Tensor): # Check if it's a tensor now
                raise TypeError(f"Audio data after concatenation is not a tensor. Got type: {type(processed_tensor)}")

            # Ensure correct shape (C, L) for torchaudio.save
            if processed_tensor.ndim == 1:  # Shape (L,)
                audio_to_save = processed_tensor.unsqueeze(0)  # Convert to (1, L)
            elif processed_tensor.ndim == 2: # Shape (C, L)
                if processed_tensor.shape[0] == 0:
                    raise ValueError(f"Audio tensor has 0 channels: {processed_tensor.shape}")
                if processed_tensor.shape[0] > 1: # If C > 1 (stereo/multi-channel)
                    print(f"Multi-channel audio (shape {processed_tensor.shape}) detected. Taking the first channel.")
                    audio_to_save = processed_tensor[0, :].unsqueeze(0) # Result is (1, L)
                else: # Already (1, L)
                    audio_to_save = processed_tensor
            else:
                raise ValueError(f"Unexpected audio tensor dimensions: {processed_tensor.ndim}, shape: {processed_tensor.shape}")
            buffer = AudioUtils.save_audio_to_buffer(audio_to_save, self.model.sr)
            duration = audio_to_save.shape[1] / self.model.sr # Use shape[1] for length
            
            # Reset buffer position for reading
            buffer.seek(0)
            # --- End of new audio processing logic ---            # Prepare processing info
            processing_info = {
                "total_chunks": len(text_chunks),
                "processed_chunks": len(audio_chunks),
                "failed_chunks": len(text_chunks) - len(audio_chunks),
                "sample_rate": self.model.sr,
                "duration": duration
            }

            print(f"Full text processing complete! Final audio duration: {duration:.2f} seconds")            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=generated_full_text_speech.wav",
                    "X-Audio-Duration": str(duration),
                    "X-Chunks-Processed": str(len(audio_chunks)),
                    "X-Total-Characters": str(len(request.text))
                }
            )

        except HTTPException as http_exc:
            print(f"HTTP exception in full text generation: {http_exc.detail}")
            raise http_exc
        except Exception as e:
            error_msg = f"Full text audio generation failed: {str(e)}"
            print(f"Exception in full text generation: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
