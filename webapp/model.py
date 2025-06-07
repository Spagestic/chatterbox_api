# Model loading and global instance for Chatterbox TTS
import os
import tempfile
import io
import base64

try:
    import modal
    # Import dependencies within the image context only if modal is available
    with modal.imports():
        import torchaudio as ta
        from chatterbox.tts import ChatterboxTTS
except (ImportError, AttributeError):
    # Fallback for local development
    try:
        import torchaudio as ta
        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        ta = None
        ChatterboxTTS = None

tts_model = None

def get_model():
    """Get or load the TTS model."""
    global tts_model
    if tts_model is None:
        if ChatterboxTTS is None:
            raise RuntimeError("ChatterboxTTS not available. Make sure dependencies are installed.")
        print("Loading Chatterbox TTS model...")
        tts_model = ChatterboxTTS.from_pretrained(device="cuda")
        print(f"Model loaded successfully! Sample rate: {tts_model.sr}")
    return tts_model
