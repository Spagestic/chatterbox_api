# TTS generation handlers for WebSocket and HTTP endpoints
import json
import os
import base64
from fastapi import WebSocket
from .model import get_model
from .audio_utils import save_temp_audio_file, audio_to_base64

async def handle_tts_generation(websocket: WebSocket, message):
    """Handle TTS generation request via WebSocket."""
    try:
        text = message.get("text", "").strip()
        voice_prompt_b64 = message.get("voice_prompt")
        if not text:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Text cannot be empty"
            }))
            return
        if len(text) > 1000:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Text too long (max 1000 characters)"
            }))
            return
        await websocket.send_text(json.dumps({
            "type": "progress",
            "progress": 10,
            "message": "Processing request..."
        }))
        audio_prompt_path = None
        if voice_prompt_b64:
            try:
                audio_data = base64.b64decode(voice_prompt_b64)
                audio_prompt_path = save_temp_audio_file(audio_data)
                await websocket.send_text(json.dumps({
                    "type": "progress",
                    "progress": 30,
                    "message": "Voice prompt processed..."
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Invalid voice prompt: {str(e)}"
                }))
                return
        await websocket.send_text(json.dumps({
            "type": "progress",
            "progress": 50,
            "message": "Generating audio..."
        }))
        print(f"Generating audio for text: {text[:50]}...")
        model = get_model()
        if audio_prompt_path:
            wav = model.generate(text, audio_prompt_path=audio_prompt_path)
            os.unlink(audio_prompt_path)
        else:
            wav = model.generate(text)
        await websocket.send_text(json.dumps({
            "type": "progress",
            "progress": 80,
            "message": "Processing audio output..."
        }))
        audio_base64 = audio_to_base64(wav)
        await websocket.send_text(json.dumps({
            "type": "progress",
            "progress": 100,
            "message": "Complete!"
        }))
        await websocket.send_text(json.dumps({
            "type": "audio_complete",
            "audio_data": audio_base64,
            "duration": len(wav[0]) / model.sr
        }))
    except Exception as e:
        print(f"Error in TTS generation: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Generation failed: {str(e)}"
        }))
