# Enhanced Chatterbox TTS API

This package contains the modular components of the Enhanced Chatterbox TTS API with GPU-accelerated processing, intelligent text chunking, and server-side audio concatenation.

## Features

- **GPU-Accelerated Processing**: Leverage server GPU for parallel chunk processing
- **Intelligent Text Chunking**: Smart text splitting that respects sentence and paragraph boundaries
- **Server-Side Concatenation**: Seamless audio merging with fade effects and silence control
- **Voice Cloning**: Optional voice prompt for personalized speech generation
- **Multiple Response Formats**: Streaming audio, complete files, or JSON with base64 encoding
- **Scalable Architecture**: Handles texts of any length efficiently

## Structure

```
api/
├── __init__.py          # Package initialization and exports
├── config.py            # Modal app configuration and container image setup
├── models.py            # Pydantic request/response models (enhanced with full-text support)
├── audio_utils.py       # Audio processing utilities and helper functions
├── text_processing.py   # Server-side text chunking and audio concatenation
├── tts_service.py       # Main TTS service class with all API endpoints
├── test_api.py          # Comprehensive API testing suite
└── README.md           # This file
```

## Components

### config.py

- Modal app configuration with GPU support (A10G)
- Container image setup with required dependencies
- Centralized configuration management
- Memory snapshot and scaling configuration

### models.py

- `TTSRequest`: Standard request model for TTS generation
- `FullTextTTSRequest`: Enhanced request model for full-text processing with chunking parameters
- `TTSResponse`: Standard response model for JSON endpoints
- `FullTextTTSResponse`: Enhanced response with processing information
- `HealthResponse`: Response model for health checks
- All models include proper type hints, validation, and documentation

### text_processing.py

- `TextChunker`: Intelligent server-side text chunking with configurable parameters
- `AudioConcatenator`: Server-side audio concatenation with fade effects and silence control
- Optimized for GPU processing and large text handling

### audio_utils.py

- `AudioUtils`: Static utility class for audio operations
- Buffer management for audio data
- Temporary file handling with automatic cleanup
- Reusable audio processing functions

### tts_service.py

- `ChatterboxTTSService`: Main service class with all endpoints
- GPU-accelerated TTS model loading and inference
- Multiple API endpoints for different use cases
- Comprehensive error handling and validation
- New full-text processing endpoints with parallel chunk processing

### test_api.py

- Comprehensive testing suite for all API endpoints
- Tests for basic generation, voice cloning, file uploads, and full-text processing
- Performance benchmarking and validation scripts

## API Endpoints

### Standard Endpoints

#### `GET /health`

Health check endpoint to verify model status and service availability.

```bash
curl -X GET "YOUR-ENDPOINT/health"
```

#### `POST /generate_audio`

Generate speech audio from text with optional voice cloning (streaming response).

```bash
curl -X POST "YOUR-ENDPOINT/generate_audio" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!"}' \
  --output output.wav
```

#### `POST /generate_json`

Generate speech and return JSON with base64 encoded audio.

```bash
curl -X POST "YOUR-ENDPOINT/generate_json" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!"}'
```

#### `POST /generate_with_file`

Generate speech with file upload for voice cloning.

```bash
curl -X POST "YOUR-ENDPOINT/generate_with_file" \
  -F "text=Hello world!" \
  -F "voice_prompt=@voice_sample.wav" \
  --output output.wav
```

### Enhanced Full-Text Endpoints

#### `POST /generate_full_text_audio`

🆕 Generate speech from full text with server-side chunking and parallel processing.

```bash
curl -X POST "YOUR-ENDPOINT/generate_full_text_audio" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your very long text here...",
    "max_chunk_size": 800,
    "silence_duration": 0.5,
    "fade_duration": 0.1,
    "overlap_sentences": 0
  }' \
  --output full_text_output.wav
```

#### `POST /generate_full_text_json`

🆕 Generate speech from full text and return JSON with processing information.

```bash
curl -X POST "YOUR-ENDPOINT/generate_full_text_json" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your very long text here...",
    "max_chunk_size": 800,
    "silence_duration": 0.5
  }'
```

### Legacy Endpoints

#### `POST /generate`

Legacy endpoint for backward compatibility.

```bash
curl -X POST "YOUR-ENDPOINT/generate?prompt=Hello%20world!" \
  --output legacy_output.wav
```

## Request Parameters

### FullTextTTSRequest Parameters

- **`text`** (required): The text to convert to speech (any length)
- **`voice_prompt_base64`** (optional): Base64 encoded voice prompt for cloning
- **`max_chunk_size`** (optional, default: 800): Maximum characters per chunk
- **`silence_duration`** (optional, default: 0.5): Silence between chunks in seconds
- **`fade_duration`** (optional, default: 0.1): Fade in/out duration in seconds
- **`overlap_sentences`** (optional, default: 0): Sentences to overlap between chunks

## Response Headers

Enhanced endpoints include additional headers with processing information:

- **`X-Audio-Duration`**: Duration of generated audio in seconds
- **`X-Chunks-Processed`**: Number of text chunks processed
- **`X-Total-Characters`**: Total characters in the input text

## Usage

```python
from api import app, ChatterboxTTSService

# The app is automatically configured and ready to deploy
# The service class contains all the endpoints
```

### Python Client Example

```python
import requests

# Generate audio from long text
response = requests.post(
    "YOUR-ENDPOINT/generate_full_text_audio",
    json={
        "text": "Your long document text here...",
        "max_chunk_size": 800,
        "silence_duration": 0.5
    }
)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("Audio generated successfully!")
```

## Performance Characteristics

### Standard Processing

- **Text Length**: Up to ~1000 characters optimal
- **Processing Time**: ~2-5 seconds per request
- **Use Case**: Short texts, real-time applications

### Full-Text Processing

- **Text Length**: Unlimited (automatically chunked)
- **Processing Time**: ~5-15 seconds for long documents
- **Parallelization**: Up to 4 concurrent chunks
- **Use Case**: Documents, articles, books

## Deployment

```bash
# Deploy the enhanced API
modal deploy tts_service.py

# Test the deployment
python test_api.py
```

````

## Benefits of Enhanced Architecture

1. **GPU Acceleration**: Server-side processing leverages GPU resources for faster inference
2. **Intelligent Chunking**: Smart text splitting that preserves sentence integrity
3. **Parallel Processing**: Multiple chunks processed simultaneously for better performance
4. **Scalability**: Handles texts of any length without client-side limitations
5. **Separation of Concerns**: Each file has a specific responsibility
6. **Maintainability**: Easier to update and modify individual components
7. **Testability**: Components can be tested in isolation
8. **Reusability**: Components can be imported and used in other projects
9. **Readability**: Smaller files are easier to understand and navigate

## Testing

Run the comprehensive test suite:

```bash
cd api/
python test_api.py
````

The test suite includes:

- Health check validation
- Basic text-to-speech generation
- JSON response testing
- Voice cloning functionality
- File upload testing
- Full-text processing validation
- Performance benchmarking

## Environment Variables

Set these environment variables for testing:

```bash
HEALTH_ENDPOINT=https://your-modal-endpoint.modal.run/health
GENERATE_AUDIO_ENDPOINT=https://your-modal-endpoint.modal.run/generate_audio
GENERATE_JSON_ENDPOINT=https://your-modal-endpoint.modal.run/generate_json
GENERATE_WITH_FILE_ENDPOINT=https://your-modal-endpoint.modal.run/generate_with_file
GENERATE_ENDPOINT=https://your-modal-endpoint.modal.run/generate
FULL_TEXT_TTS_ENDPOINT=https://your-modal-endpoint.modal.run/generate_full_text_audio
FULL_TEXT_JSON_ENDPOINT=https://your-modal-endpoint.modal.run/generate_full_text_json
```
