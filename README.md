# Chatterbox TTS Modal API

An advanced text-to-speech API powered by Chatterbox TTS, deployed on Modal with GPU acceleration. This enhanced version provides multiple endpoints, voice cloning capabilities, and comprehensive error handling.

## Table of Contents

- [Chatterbox TTS Modal API](#chatterbox-tts-modal-api)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Quick Start](#quick-start)
    - [1. Deploy to Modal](#1-deploy-to-modal)
    - [2. Test the API](#2-test-the-api)
  - [API Endpoints](#api-endpoints)
    - [Health Check](#health-check)
    - [Generate Audio (Streaming)](#generate-audio-streaming)
    - [Generate Audio (JSON Response)](#generate-audio-json-response)
    - [Generate with File Upload](#generate-with-file-upload)
    - [Legacy Endpoint](#legacy-endpoint)
  - [Usage Examples](#usage-examples)
    - [Python Client](#python-client)
    - [cURL Examples](#curl-examples)
    - [JavaScript/Node.js](#javascriptnodejs)
  - [Request/Response Formats](#requestresponse-formats)
    - [TTSRequest](#ttsrequest)
    - [TTSResponse](#ttsresponse)
    - [HealthResponse](#healthresponse)
  - [Error Handling](#error-handling)
  - [Performance](#performance)
  - [Voice Cloning](#voice-cloning)
  - [Development](#development)
    - [Local Testing](#local-testing)
    - [Configuration](#configuration)
  - [API Documentation](#api-documentation)
  - [License](#license)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Getting Help](#getting-help)
  - [Contributing](#contributing)
  - [Changelog](#changelog)
    - [v2.0.0 (Enhanced Version)](#v200-enhanced-version)

## Features

- 🎯 **Multiple API Endpoints** - Choose between streaming, JSON, or file upload interfaces
- 🎭 **Voice Cloning** - Use custom audio prompts to clone voices
- 🛡️ **Error Handling** - Comprehensive validation and error messages
- 📊 **Health Monitoring** - Built-in health check endpoint
- 📚 **API Documentation** - Auto-generated OpenAPI/Swagger docs
- 🔄 **Backward Compatibility** - Legacy endpoint still supported
- ⚡ **GPU Acceleration** - Fast inference with A10G GPU
- 🏗️ **Scalable** - Auto-scaling with configurable concurrency

## Quick Start

### 1. Deploy to Modal

```bash
modal deploy chatterbox_tts.py
```

### 2. Test the API

Update the `BASE_URL` in `test_api.py` with your Modal endpoint and run:

```bash
python test_api.py
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the status of the API and model loading state.

### Generate Audio (Streaming)

```bash
POST /generate_audio
Content-Type: application/json

{
  "text": "Hello, world!",
  "voice_prompt_base64": "optional_base64_encoded_audio"
}
```

Returns audio file as streaming response.

### Generate Audio (JSON Response)

```bash
POST /generate_json
Content-Type: application/json

{
  "text": "Hello, world!",
  "voice_prompt_base64": "optional_base64_encoded_audio"
}
```

Returns JSON with base64-encoded audio data and metadata.

### Generate with File Upload

```bash
POST /generate_with_file
Content-Type: multipart/form-data

text=Hello, world!
voice_prompt=@voice_sample.wav
```

Upload audio files directly for voice cloning.

### Legacy Endpoint

```bash
POST /generate
Content-Type: application/x-www-form-urlencoded

prompt=Hello, world!
```

Maintains backward compatibility with the original API.

## Usage Examples

### Python Client

```python
import requests
import base64

# Basic text-to-speech
response = requests.post(
    "YOUR-ENDPOINT-URL/generate_audio",
    json={"text": "Hello from Python!"}
)
with open("output.wav", "wb") as f:
    f.write(response.content)

# Voice cloning with base64
with open("voice_sample.wav", "rb") as f:
    voice_data = base64.b64encode(f.read()).decode()

response = requests.post(
    "YOUR-ENDPOINT-URL/generate_audio",
    json={
        "text": "This will sound like the voice sample!",
        "voice_prompt_base64": voice_data
    }
)
with open("cloned_voice.wav", "wb") as f:
    f.write(response.content)

# JSON response
response = requests.post(
    "YOUR-ENDPOINT-URL/generate_json",
    json={"text": "Return as JSON"}
)
data = response.json()
if data['success']:
    audio_data = base64.b64decode(data['audio_base64'])
    with open("json_output.wav", "wb") as f:
        f.write(audio_data)
    print(f"Duration: {data['duration_seconds']:.2f} seconds")
```

### cURL Examples

```bash
# Health check
curl -X GET "YOUR-ENDPOINT-URL/health"

# Basic generation
curl -X POST "YOUR-ENDPOINT-URL/generate_audio" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!"}' \
  --output output.wav

# With voice prompt file
curl -X POST "YOUR-ENDPOINT-URL/generate_with_file" \
  -F "text=Clone this voice!" \
  -F "voice_prompt=@voice_sample.wav" \
  --output cloned.wav

# JSON response
curl -X POST "YOUR-ENDPOINT-URL/generate_json" \
  -H "Content-Type: application/json" \
  -d '{"text": "JSON response"}' \
  | jq -r '.audio_base64' | base64 -d > json_output.wav
```

### JavaScript/Node.js

```javascript
// Basic generation
const response = await fetch("YOUR-ENDPOINT-URL/generate_audio", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "Hello from JavaScript!" }),
});

const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);

// Play in browser
const audio = new Audio(audioUrl);
audio.play();

// Voice cloning with file
const formData = new FormData();
formData.append("text", "Clone this voice!");
formData.append("voice_prompt", fileInput.files[0]);

const clonedResponse = await fetch("YOUR-ENDPOINT-URL/generate_with_file", {
  method: "POST",
  body: formData,
});
```

## Request/Response Formats

### TTSRequest

```json
{
  "text": "string (required, max 1000 chars)",
  "voice_prompt_base64": "string (optional, base64 encoded audio)"
}
```

### TTSResponse

```json
{
  "success": "boolean",
  "message": "string",
  "audio_base64": "string (base64 encoded WAV)",
  "duration_seconds": "number"
}
```

### HealthResponse

```json
{
  "status": "string",
  "model_loaded": "boolean"
}
```

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request` - Invalid input (empty text, too long, invalid audio)
- `500 Internal Server Error` - Model or generation errors

Error responses include descriptive messages to help diagnose issues.

## Performance

- **Cold Start**: ~30 seconds (model loading with memory snapshots)
- **Generation Time**: 2-3 seconds for 5-second audio clips
- **Concurrency**: Up to 10 concurrent requests per container
- **Auto-scaling**: Containers scale down after 5 minutes of inactivity
- **GPU**: NVIDIA A10G for fast inference

## Voice Cloning

The API supports voice cloning through audio prompts:

1. **Supported Formats**: WAV, MP3, MPEG
2. **Upload Methods**:
   - Base64 encoding in JSON requests
   - Direct file upload via multipart/form-data
3. **Quality Tips**:
   - Use clear, high-quality audio samples
   - 5-30 seconds of speech works best
   - Single speaker recordings preferred

## Development

### Local Testing

1. Install dependencies:

```bash
pip install modal requests
```

2. Set up Modal:

```bash
modal token new
```

3. Deploy the app:

```bash
modal deploy chatterbox_tts.py
```

4. Run tests:

```bash
python test_api.py
```

### Configuration

The Modal app is configured with:

- GPU: NVIDIA A10G
- Python: 3.12
- Concurrent requests: 10 per container
- Scale-down window: 5 minutes
- Memory snapshots: Enabled

## API Documentation

Once deployed, visit `YOUR-ENDPOINT-URL/docs` for interactive Swagger documentation.

## License

This project uses the Chatterbox TTS model. Please refer to the [Chatterbox repository](https://github.com/resemble-ai/chatterbox) for licensing information.

## Troubleshooting

### Common Issues

1. **Model Loading Errors**: Ensure GPU memory is sufficient
2. **Audio Format Issues**: Verify uploaded files are valid audio
3. **Timeout Errors**: Large texts may take longer to process
4. **Memory Issues**: Large audio prompts may cause OOM errors

### Getting Help

- Check the `/health` endpoint for model status
- Review logs in Modal dashboard
- Ensure your audio files are in supported formats
- Verify text length is under 1000 characters

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes with `test_api.py`
4. Submit a pull request

## Changelog

### v2.0.0 (Enhanced Version)

- Added multiple API endpoints
- Voice cloning support
- Comprehensive error handling
- Health monitoring
- Request/response validation
- Enhanced documentation
- Backward compatibility maintained
