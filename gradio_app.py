"""
Gradio App for Chatterbox TTS API
A user-friendly interface to interact with the Chatterbox TTS Modal API.
"""

import os
import base64
import tempfile
import io
import requests
import gradio as gr
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
import soundfile as sf

# Import refactored components
from components.check_api_health import check_api_health
from components.generate_tts_audio import generate_tts_audio
from components.generate_sample_text import generate_sample_text
from components.update_char_count import update_char_count
from components.custom_css import custom_css

# Load environment variables
load_dotenv()

# API Endpoints from environment variables
GENERATE_AUDIO_ENDPOINT = os.getenv("GENERATE_AUDIO_ENDPOINT")
GENERATE_WITH_FILE_ENDPOINT = os.getenv("GENERATE_WITH_FILE_ENDPOINT")
HEALTH_ENDPOINT = os.getenv("HEALTH_ENDPOINT")

# Default endpoint if not in env (user will need to update this)
if not GENERATE_AUDIO_ENDPOINT:
    GENERATE_AUDIO_ENDPOINT = "YOUR-MODAL-ENDPOINT-URL/generate_audio"
if not GENERATE_WITH_FILE_ENDPOINT:
    GENERATE_WITH_FILE_ENDPOINT = "YOUR-MODAL-ENDPOINT-URL/generate_with_file"
if not HEALTH_ENDPOINT:
    HEALTH_ENDPOINT = "YOUR-MODAL-ENDPOINT-URL/health"

# Create the Gradio interface
with gr.Blocks(css=custom_css, title="Chatterbox TTS API Demo") as demo:
    gr.Markdown(
        """
        # 🗣️ Chatterbox TTS API Demo
        
        Generate high-quality speech from text using the Chatterbox TTS model deployed on Modal.
        
        **Features:**
        - Convert text to speech with natural-sounding voices
        - Voice cloning with reference audio samples
        - Powered by Modal's serverless GPU infrastructure
        """
    )
    
    # API Status Section
    with gr.Row():
        with gr.Column():
            api_status = gr.Textbox(
                label="🔍 API Status",
                value=check_api_health(),
                interactive=False,
                elem_classes=["status-box"]
            )
            refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📝 Input")
            text = gr.Textbox(
                value="Hello! This is a test of the Chatterbox TTS system running on Modal.",
                label="Text to synthesize",
                placeholder="Enter the text you want to convert to speech (max 1000 characters)",
                lines=4,
                max_lines=8
            )
            
            with gr.Row():
                sample_btn = gr.Button("🎲 Random Sample", size="sm")
                char_count = gr.Textbox(
                                    value="0/1000", 
                    label="Character Count", 
                    interactive=False,
                    scale=0
                )
            
            gr.Markdown("### 🎤 Voice Cloning (Optional)")
            ref_wav = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Reference Audio File"
            )
            
            gr.Markdown(
                """
                **Voice Cloning Tips:**
                - Use clear, high-quality audio (5-30 seconds)
                - Single speaker recordings work best
                - Supported formats: WAV, MP3, MPEG
                """
            )
            
            generate_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg")

        with gr.Column():
            gr.Markdown("### 🔊 Generated Audio")
            audio_output = gr.Audio(
                label="Generated Speech",
                interactive=False
            )
            
            gr.Markdown("### ℹ️ Instructions")
            gr.Markdown(
                """
                1. **Enter Text**: Type or paste the text you want to convert to speech
                2. **Optional Voice Cloning**: Upload a reference audio file to clone a specific voice
                3. **Generate**: Click the generate button and wait for the audio to be created
                4. **Play**: Use the audio player to listen to the generated speech
                
                **Note**: Generation may take 30+ seconds on cold start as the model loads.
                """
            )

    # Event handlers
    text.change(
        fn=update_char_count,
        inputs=[text],
        outputs=[char_count]
    )
    
    sample_btn.click(
        fn=generate_sample_text,
        outputs=[text]
    )
    
    refresh_status_btn.click(
        fn=check_api_health,
        outputs=[api_status]
    )
    
    generate_btn.click(
        fn=generate_tts_audio,
        inputs=[text, ref_wav],
        outputs=[audio_output],
        show_progress=True
    )

# Launch configuration
if __name__ == "__main__":
    print("🚀 Starting Chatterbox TTS Gradio App...")
    print(f"📡 API Endpoint: {GENERATE_AUDIO_ENDPOINT}")
    print(f"🔊 Voice Clone Endpoint: {GENERATE_WITH_FILE_ENDPOINT}")
    
    demo.launch(
        server_port=7860,       # Default Gradio port
        share=False,            # Set to True for public sharing
        debug=True              # Enable debug mode
    )
