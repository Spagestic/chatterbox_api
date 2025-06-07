
"""
Audio processing utilities for TTS service.
"""

import io
import tempfile
import os
from .config import image

with image.imports():
    import torchaudio as ta


class AudioUtils:
    """Helper class for audio processing operations."""
    
    @staticmethod
    def save_audio_to_buffer(wav_tensor, sample_rate: int) -> io.BytesIO:
        """
        Save audio tensor to BytesIO buffer.
        
        Args:
            wav_tensor: Audio tensor to save
            sample_rate: Sample rate of the audio
            
        Returns:
            BytesIO buffer containing WAV audio data
        """
        buffer = io.BytesIO()
        ta.save(buffer, wav_tensor, sample_rate, format="wav")
        buffer.seek(0)
        return buffer

    @staticmethod
    def save_temp_audio_file(audio_data: bytes) -> str:
        """
        Save uploaded audio data to a temporary file.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            Path to the temporary audio file
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            return temp_file.name

    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """
        Clean up temporary audio file.
        
        Args:
            file_path: Path to the temporary file to delete
        """
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp file {file_path}: {e}")
