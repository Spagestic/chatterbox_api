
"""
Modal app configuration and container image setup.
"""

import modal

# Define a container image with required dependencies
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "chatterbox-tts==0.1.1", "fastapi[standard]", "pydantic", "numpy"
)

# Create the Modal app
app = modal.App("chatterbox-api-example", image=image)
