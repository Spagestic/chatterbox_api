# FastAPI route definitions for Chatterbox TTS Web App
import io
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from .html_template import HTML_TEMPLATE
from .model import tts_model, get_model
from .audio_utils import save_temp_audio_file
from .tts_handlers import handle_tts_generation


def create_web_app():
    web_app = FastAPI(title="Chatterbox TTS Web App")

    @web_app.get("/")
    async def serve_web_app():
        return HTMLResponse(content=HTML_TEMPLATE)

    @web_app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "model_loaded": tts_model is not None
        }

    @web_app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        print("WebSocket connection established")
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get("type") == "generate_tts":
                    await handle_tts_generation(websocket, message)
        except WebSocketDisconnect:
            print("WebSocket disconnected")
        except Exception as e:
            print(f"WebSocket error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))

    @web_app.post("/generate_streaming")
    async def generate_streaming(
        text: str = Form(...),
        voice_prompt: UploadFile = File(None)
    ):
        try:
            if not text or len(text.strip()) == 0:
                raise HTTPException(status_code=400, detail="Text cannot be empty")
            if len(text) > 1000:
                raise HTTPException(status_code=400, detail="Text too long (max 1000 characters)")
            audio_prompt_path = None
            if voice_prompt:
                audio_data = await voice_prompt.read()
                audio_prompt_path = save_temp_audio_file(audio_data)            
                print(f"Generating audio for text: {text[:50]}...")
            model = get_model()
            if audio_prompt_path:
                wav = model.generate(text, audio_prompt_path=audio_prompt_path)
                os.unlink(audio_prompt_path)
            else:
                wav = model.generate(text)
            
            # Import torchaudio safely
            try:
                import modal
                with modal.imports():
                    import torchaudio as ta
            except (ImportError, AttributeError):
                import torchaudio as ta
            
            buffer = io.BytesIO()
            ta.save(buffer, wav, model.sr, format="wav")
            buffer.seek(0)
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=generated_speech.wav",
                    "X-Audio-Duration": str(len(wav[0]) / model.sr)
                }
            )
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
    return web_app
