# API Package

This package contains the modular components of the Chatterbox TTS API.

## Structure

```
api/
├── __init__.py          # Package initialization and exports
├── config.py            # Modal app configuration and container image setup
├── models.py            # Pydantic request/response models
├── audio_utils.py       # Audio processing utilities and helper functions
├── tts_service.py       # Main TTS service class with all API endpoints
└── README.md           # This file
```

## Components

### config.py

- Modal app configuration
- Container image setup with required dependencies
- Centralized configuration management

### models.py

- `TTSRequest`: Request model for TTS generation
- `TTSResponse`: Response model for JSON endpoints
- `HealthResponse`: Response model for health checks
- All models include proper type hints and documentation

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

## Usage

```python
from api import app, ChatterboxTTSService

# The app is automatically configured and ready to deploy
# The service class contains all the endpoints
```

## Benefits of Modular Architecture

1. **Separation of Concerns**: Each file has a specific responsibility
2. **Maintainability**: Easier to update and modify individual components
3. **Testability**: Components can be tested in isolation
4. **Reusability**: Components can be imported and used in other projects
5. **Readability**: Smaller files are easier to understand and navigate
