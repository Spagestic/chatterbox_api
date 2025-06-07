# ---
# deploy: true
# cmd: ["modal", "serve", "chatterbox_webapp.py"]
# ---

"""
Chatterbox TTS Web App on Modal with Real-time Audio Streaming

This Modal app combines the Chatterbox TTS model with a web interface that supports
real-time audio streaming. Users can input text and hear audio as it's being generated,
without waiting for the complete generation to finish.

Key Features:
- Integrated web interface served directly from Modal
- Real-time audio streaming using WebSockets
- Voice cloning support with file upload
- Modern, responsive UI with progress indicators
- No external API calls - everything runs in the same container
"""

from pathlib import Path
import modal
from webapp import create_web_app

# Define the container image with all dependencies
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "chatterbox-tts==0.1.1", 
    "fastapi[standard]", 
    "pydantic", 
    "numpy",
    "websockets",
    "python-multipart"
)

# Add the webapp directory to the image so it's available in the container
local_webapp_path = Path(__file__).parent / "webapp"
image = image.add_local_dir(local_webapp_path, remote_path="/webapp")

app = modal.App("chatterbox-webapp")

@app.function(
    image=image,
    gpu="a10g",
    scaledown_window=60 * 5,
    enable_memory_snapshot=True,
    container_idle_timeout=300
)
@modal.asgi_app()
def web():
    return create_web_app()

# Deployment instructions
if __name__ == "__main__":
    print("Deploy this app with: modal deploy chatterbox_webapp.py")
    print("The web app will be available at the provided URL after deployment.")
