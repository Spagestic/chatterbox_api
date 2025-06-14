
"""
Modal app configuration and container image setup.
"""

import modal

# Define a container image with required dependencies
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "chatterbox-tts==0.1.1", 
    "fastapi[standard]", 
    "pydantic", 
    "numpy",
    "transformers>=4.45.0,<4.47.0",  # Pin to avoid deprecation warnings
    "torch>=2.0.0",
    "torchaudio>=2.0.0"
).env({
    # Suppress the specific transformers deprecation warning
    "PYTHONWARNINGS": "ignore::FutureWarning:transformers"
})

# Create the Modal app
app = modal.App("chatterbox-api-example", image=image)
