# ---
# output-directory: "/tmp/chatterbox-tts"
# lambda-test: false
# cmd: ["modal", "serve", "06_gpu_and_ml/test-to-audio/chatterbox_tts.py"]
# ---


# # Enhanced Chatterbox TTS API on Modal

# This example demonstrates how to deploy an advanced text-to-speech (TTS) API using the Chatterbox TTS model on Modal.
# The API provides multiple endpoints for different use cases including voice cloning, file uploads, and JSON responses.
# 
# Key Features:
# - Multiple API endpoints (streaming, JSON, file upload)
# - Voice cloning with custom audio prompts
# - Comprehensive error handling and validation
# - Health monitoring endpoint
# - Request/response models with Pydantic
# - Backward compatibility with legacy endpoints
# - Enhanced documentation and examples
# - Modular architecture with separate components
#
# We use Modal's class-based approach with GPU acceleration to provide fast, scalable TTS inference.

# ## Setup

# Import the modular API components from the api package.

from api import app, ChatterboxTTSService

# The TTS service is now implemented in a modular structure with components in the api/ folder:
# - api/config.py: Modal app configuration and container image setup
# - api/models.py: Pydantic request/response models  
# - api/audio_utils.py: Audio processing utilities
# - api/tts_service.py: Main TTS service class with all endpoints


# ## Deployment and Usage

# Deploy the enhanced Chatterbox API with:
#
# ```shell
# modal deploy chatterbox_tts.py
# ```
#
# The modular structure provides several benefits:
# - **Maintainability**: Each component has a single responsibility
# - **Testability**: Individual components can be tested in isolation  
# - **Reusability**: Components can be imported and used in other projects
# - **Readability**: Smaller files are easier to understand and navigate
#
# ## Modular Architecture
#
# - `api/config.py`: Modal app configuration and container image setup
# - `api/models.py`: Pydantic request/response models for validation
# - `api/audio_utils.py`: Audio processing utilities and helper functions
# - `api/tts_service.py`: Main TTS service class with all API endpoints
# - `api/__init__.py`: Package initialization and exports
#
# ## API Endpoints
#
# The API provides multiple endpoints for different use cases:
#
# ### 1. Health Check
# ```shell
# curl -X GET "<YOUR-ENDPOINT-URL>/health"
# ```
#
# ### 2. Generate Audio (Streaming Response)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_audio" \
#   -H "Content-Type: application/json" \
#   -d '{"text": "Hello, this is Chatterbox TTS running on Modal!"}' \
#   --output output.wav
# ```
#
# ### 3. Generate Audio (Direct File Response)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_audio_file" \
#   -H "Content-Type: application/json" \
#   -d '{"text": "Hello, this is the non-streaming endpoint!"}' \
#   --output direct_output.wav
# ```
#
# ### 4. Generate Audio with Voice Prompt (File Upload)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_with_file" \
#   -F "text=Hello, this is voice cloning with Chatterbox!" \
#   -F "voice_prompt=@your_voice_sample.wav" \
#   --output cloned_voice.wav
# ```
#
# ### 5. Generate Audio (JSON Response with Base64)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate_json" \
#   -H "Content-Type: application/json" \
#   -d '{"text": "This returns JSON with base64 audio data"}' \
#   | jq -r '.audio_base64' | base64 -d > output.wav
# ```
#
# ### 6. Legacy Endpoint (Backward Compatibility)
# ```shell
# curl -X POST "<YOUR-ENDPOINT-URL>/generate" \
#   --data-urlencode "prompt=Legacy endpoint still works!" \
#   --output legacy_output.wav
# ```
#
# ## Python Client Example
#
# ```python
# import requests
# import base64
# import json
#
# # Basic text-to-speech (streaming)
# response = requests.post(
#     "YOUR-ENDPOINT-URL/generate_audio",
#     json={"text": "Hello from Python!"}
# )
# with open("python_output.wav", "wb") as f:
#     f.write(response.content)
#
# # Basic text-to-speech (direct file)
# response = requests.post(
#     "YOUR-ENDPOINT-URL/generate_audio_file",
#     json={"text": "Hello from Python using direct file endpoint!"}
# )
# with open("python_direct_output.wav", "wb") as f:
#     f.write(response.content)
#
# # With voice prompt (base64 encoded)
# with open("voice_sample.wav", "rb") as f:
#     voice_data = base64.b64encode(f.read()).decode()
#
# response = requests.post(
#     "YOUR-ENDPOINT-URL/generate_audio", 
#     json={
#         "text": "This will sound like the provided voice sample!",
#         "voice_prompt_base64": voice_data
#     }
# )
# with open("cloned_output.wav", "wb") as f:
#     f.write(response.content)
# ```
#
# ## Features
#
# - **Multiple Endpoints**: Choose between direct file responses, streaming, JSON responses, or file uploads
# - **Voice Cloning**: Upload audio samples to clone voices using the voice prompt feature
# - **Error Handling**: Comprehensive error messages and status codes
# - **Health Monitoring**: Health check endpoint for monitoring deployments
# - **Request Validation**: Input validation with clear error messages
# - **Backward Compatibility**: Legacy endpoint still supported
# - **Enhanced Documentation**: OpenAPI/Swagger docs available at `/docs`
# - **Modular Architecture**: Clean separation of concerns for maintainability
#
# ## Performance
#
# This enhanced app maintains the same performance characteristics:
# - ~30 seconds cold boot time (model loading)
# - 2-3 seconds to generate a 5-second audio clip
# - Up to 10 concurrent requests per container
# - 5-minute scale-down window for cost efficiency
# - Memory snapshots enabled for faster cold starts
