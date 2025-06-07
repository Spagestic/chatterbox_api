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

# Function to accumulate audio stream
def add_to_stream(audio, instream):
    """Accumulate streaming audio data"""
    import numpy as np
    if audio is None:
        return None, instream
    if instream is None:
        ret = audio
    else:
        # Concatenate audio data
        ret = (audio[0], np.concatenate((instream[1], audio[1])))
    return ret, ret

def save_streamed_audio(stream_state):
    """Convert streamed audio to file format"""
    if stream_state is None:
        return None
    
    try:
        sample_rate, audio_data = stream_state
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"streamed_audio_{np.random.randint(1000, 9999)}.wav")
        
        # Save audio data to file
        sf.write(temp_file, audio_data, sample_rate)
        return temp_file
    except Exception as e:
        print(f"Error saving streamed audio: {e}")
        return None

def clear_stream():
    """Clear the audio stream state"""
    return None, None

# Create the Gradio interface
with gr.Blocks(css=custom_css, title="Chatterbox TTS API Demo") as demo:
    gr.Markdown(
        """
        # 🗣️ Chatterbox TTS API Demo
        
        Generate high-quality speech from text using the Chatterbox TTS model deployed on Modal.
        """,
        elem_id="main-title"
    )
    
    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 Input")
            text = gr.Textbox(
                value="Hello! This is a test of the Chatterbox TTS system running on Modal.",
                label="Text to synthesize",
                placeholder="Enter the text you want to convert to speech (max 1000 characters)",
                lines=4,
                max_lines=8,
                elem_id="input-textbox"
            )
            with gr.Row():
                sample_btn = gr.Button("🎲 Random Sample", size="sm", variant="secondary")
                char_count = gr.Textbox(
                    value="0/1000", 
                    label="Character Count", 
                    interactive=False,
                    scale=0,
                    elem_id="char-count-box"
                )
            gr.Markdown("---")
            with gr.Accordion("🎤 Voice Cloning (Optional)", open=False):
                # Streaming audio input (microphone or upload)
                ref_wav = gr.Audio(
                    sources=["upload", "microphone"],
                    type="numpy",
                    streaming=True,
                    autoplay=True,
                    label="Reference Audio File"
                )
                # State to accumulate audio stream
                stream_state = gr.State(value=None)
                gr.Markdown(
                    """
                    **Voice Cloning Tips:**
                    - Use clear, high-quality audio (5-30 seconds)
                    - Single speaker recordings work best
                    - Supported formats: WAV, MP3, MPEG
                    """
                )
            gr.Markdown("---")
            generate_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg", elem_id="generate-btn")

        with gr.Column(scale=1):
            gr.Markdown("### 🔊 Generated Audio")
            audio_output = gr.Audio(
                label="Generated Speech",
                interactive=False,
                elem_id="audio-output-box"
            )
            gr.Markdown("---")
            gr.Markdown(
                """
                ### ℹ️ Instructions
                1. **Enter Text**: Type or paste the text you want to convert to speech  
                2. **Optional Voice Cloning**: Upload a reference audio file to clone a specific voice  
                3. **Generate**: Click the generate button and wait for the audio to be created  
                4. **Play**: Use the audio player to listen to the generated speech
                
                **Note**: Generation may take 30+ seconds on cold start as the model loads.
                """
            )
    
    gr.Markdown("---")
    gr.Markdown(
        "<div style='text-align:center; color: #888; font-size: 0.95em;'>Made with ❤️ by Chatterbox | Powered by Modal & Gradio</div>",
        elem_id="footer"
    )

    # Function to accumulate audio stream
    def add_to_stream(audio, instream):
        import numpy as np
        if audio is None:
            return None, instream
        if instream is None:
            ret = audio
        else:
            # Concatenate audio data
            ret = (audio[0], np.concatenate((instream[1], audio[1])))
        return ret, ret

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

    # Stream audio from microphone/upload and accumulate in state
    ref_wav.stream(add_to_stream, [ref_wav, stream_state], [ref_wav, stream_state])
    
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
        # server_port=7860,       # Default Gradio port
        share=False,            # Set to True for public sharing
        debug=True              # Enable debug mode
    )
