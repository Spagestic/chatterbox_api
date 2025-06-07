# Audio utility functions for Chatterbox TTS Web App
import io
import base64
import tempfile
import os
from .model import get_model

try:
    import modal
    with modal.imports():
        import torchaudio as ta
except (ImportError, AttributeError):
    # Fallback for local development
    try:
        import torchaudio as ta
    except ImportError:
        ta = None

def save_temp_audio_file(audio_data: bytes) -> str:
    """Save uploaded audio data to a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(audio_data)
        return temp_file.name

def audio_to_base64(wav_tensor) -> str:
    """Convert audio tensor to base64 string."""
    if ta is None:
        raise RuntimeError("torchaudio not available")
    model = get_model()
    buffer = io.BytesIO()
    ta.save(buffer, wav_tensor, model.sr, format="wav")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')
