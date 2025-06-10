#!/usr/bin/env python3
"""
Test script for the enhanced Chatterbox TTS Modal API
This script demonstrates how to interact with all the new endpoints
"""

import requests
import base64
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base URLs for the deployed endpoints
ENDPOINTS = {
    "health": os.getenv("HEALTH_ENDPOINT"),
    "generate_audio": os.getenv("GENERATE_AUDIO_ENDPOINT"),
    "generate_json": os.getenv("GENERATE_JSON_ENDPOINT"),
    "generate_with_file": os.getenv("GENERATE_WITH_FILE_ENDPOINT"),
    "generate": os.getenv("GENERATE_ENDPOINT"),
    "generate_full_text_audio": os.getenv("GENERATE_FULL_TEXT_AUDIO_ENDPOINT"),
    "generate_full_text_json": os.getenv("GENERATE_FULL_TEXT_JSON_ENDPOINT")
}

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(ENDPOINTS["health"])
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_basic_generation():
    """Test basic text-to-speech generation"""
    print("\nTesting basic audio generation...")
    try:
        response = requests.post(
            ENDPOINTS["generate_audio"],
            json={"text": "Hello, this is Chatterbox TTS running on Modal!"}
        )
        if response.status_code == 200:
            Path("output").mkdir(exist_ok=True)
            with open("output/basic_output.wav", "wb") as f:
                f.write(response.content)
            print("✓ Basic generation successful - saved as output/basic_output.wav")
            return True
        else:
            print(f"✗ Basic generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Basic generation error: {e}")
        return False

def test_json_generation():
    """Test JSON response with base64 audio"""
    print("\nTesting JSON audio generation...")
    try:
        response = requests.post(
            ENDPOINTS["generate_json"],
            json={"text": "This returns JSON with base64 audio data"}
        )
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['audio_base64']:
                # Decode base64 audio and save
                Path("output").mkdir(exist_ok=True)
                audio_data = base64.b64decode(data['audio_base64'])
                with open("output/json_output.wav", "wb") as f:
                    f.write(audio_data)
                print(f"✓ JSON generation successful - Duration: {data['duration_seconds']:.2f}s")
                print("  Saved as output/json_output.wav")
                return True
            else:
                print(f"✗ JSON generation failed: {data['message']}")
                return False
        else:
            print(f"✗ JSON generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ JSON generation error: {e}")
        return False

def test_voice_cloning():
    """Test voice cloning with audio prompt"""
    print("\nTesting voice cloning...")
    
    # First, check if we have a sample audio file
    sample_file = Path("voice_sample.wav")
    if not sample_file.exists():
        print("⚠ No voice_sample.wav found - skipping voice cloning test")
        print("  To test voice cloning, add a voice_sample.wav file")
        return True
    
    try:
        # Read the voice sample and encode as base64
        with open(sample_file, "rb") as f:
            voice_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            ENDPOINTS["generate_audio"],
            json={
                "text": "This should sound like the provided voice sample!",
                "voice_prompt_base64": voice_data
            }
        )
        
        if response.status_code == 200:
            Path("output").mkdir(exist_ok=True)
            with open("output/cloned_output.wav", "wb") as f:
                f.write(response.content)
            print("✓ Voice cloning successful - saved as output/cloned_output.wav")
            return True
        else:
            print(f"✗ Voice cloning failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Voice cloning error: {e}")
        return False

def test_file_upload():
    """Test file upload endpoint"""
    print("\nTesting file upload...")
    
    sample_file = Path("voice_sample.wav")
    if not sample_file.exists():
        print("⚠ No voice_sample.wav found - testing without voice prompt")
        files = None
    else:
        files = {"voice_prompt": open(sample_file, "rb")}
    
    try:
        data = {"text": "Testing the file upload endpoint!"}
        response = requests.post(ENDPOINTS["generate_with_file"], data=data, files=files)
        
        if files:
            files["voice_prompt"].close()
        
        if response.status_code == 200:
            Path("output").mkdir(exist_ok=True)
            with open("output/upload_output.wav", "wb") as f:
                f.write(response.content)
            print("✓ File upload successful - saved as output/upload_output.wav")
            return True
        else:
            print(f"✗ File upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ File upload error: {e}")
        return False

def test_legacy_endpoint():
    """Test backward compatibility with legacy endpoint"""
    print("\nTesting legacy endpoint...")
    try:
        # Legacy endpoint expects query parameters, not form data
        response = requests.post(
            ENDPOINTS["generate"],
            params={"prompt": "Testing the legacy endpoint for backward compatibility"}
        )
        if response.status_code == 200:
            Path("output").mkdir(exist_ok=True)
            with open("output/legacy_output.wav", "wb") as f:
                f.write(response.content)
            print("✓ Legacy endpoint successful - saved as output/legacy_output.wav")
            return True
        else:
            print(f"✗ Legacy endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Legacy endpoint error: {e}")
        return False

def test_full_text_generation():
    """Test full-text audio generation with server-side chunking"""
    print("\nTesting full-text audio generation...")
    
    # Create a long text that will require chunking
    long_text = """
    This is a comprehensive test of the full-text audio generation endpoint. 
    The text is intentionally long to demonstrate the server-side chunking capabilities.
    
    The enhanced API will automatically split this text into appropriate chunks,
    process them in parallel using GPU acceleration, and then concatenate the
    resulting audio segments with proper transitions and fade effects.
    
    This approach significantly improves performance for long documents while
    maintaining high audio quality and natural speech flow. The server handles
    all the complex processing, allowing the client to simply send the full text
    and receive the final audio file.
    
    The chunking algorithm respects sentence and paragraph boundaries to ensure
    natural speech patterns and maintains proper context across chunk boundaries.
    This results in more natural-sounding speech for long-form content.
    """
    
    try:
        if not ENDPOINTS["generate_full_text_audio"]:
            print("⚠ FULL_TEXT_TTS_ENDPOINT not configured - skipping full-text test")
            return True
            
        response = requests.post(
            ENDPOINTS["generate_full_text_audio"],
            json={
                "text": long_text.strip(),
                "max_chunk_size": 400,  # Smaller chunks for testing
                "silence_duration": 0.3,
                "fade_duration": 0.1,
                "overlap_sentences": 0
            },
            timeout=120  # Longer timeout for processing
        )
        
        if response.status_code == 200:
            Path("output").mkdir(exist_ok=True)
            with open("output/full_text_output.wav", "wb") as f:
                f.write(response.content)
            
            # Check response headers for processing info
            duration = response.headers.get('X-Audio-Duration', 'unknown')
            chunks = response.headers.get('X-Chunks-Processed', 'unknown')
            characters = response.headers.get('X-Total-Characters', len(long_text))
            
            print(f"✓ Full-text generation successful")
            print(f"  Duration: {duration}s")
            print(f"  Chunks processed: {chunks}")
            print(f"  Characters: {characters}")
            print("  Saved as output/full_text_output.wav")
            return True
        else:
            print(f"✗ Full-text generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Full-text generation timed out (this may be normal for very long texts)")
        return False
    except Exception as e:
        print(f"✗ Full-text generation error: {e}")
        return False


def test_full_text_json():
    """Test full-text JSON response with processing information"""
    print("\nTesting full-text JSON response...")
    
    test_text = """
    This is a test of the full-text JSON endpoint that returns detailed
    processing information along with the base64 encoded audio data.
    
    The response includes chunk information, processing parameters,
    and timing details that can be useful for monitoring and debugging.
    """
    
    try:
        if not ENDPOINTS["generate_full_text_json"]:
            print("⚠ FULL_TEXT_JSON_ENDPOINT not configured - skipping test")
            return True
            
        response = requests.post(
            ENDPOINTS["generate_full_text_json"],
            json={
                "text": test_text.strip(),
                "max_chunk_size": 300,
                "silence_duration": 0.4,
                "fade_duration": 0.15
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['audio_base64']:
                # Decode and save audio
                Path("output").mkdir(exist_ok=True)
                audio_data = base64.b64decode(data['audio_base64'])
                with open("output/full_text_json_output.wav", "wb") as f:
                    f.write(audio_data)
                
                # Display processing information
                print(f"✓ Full-text JSON generation successful")
                print(f"  Duration: {data['duration_seconds']:.2f}s")
                
                if 'processing_info' in data:
                    info = data['processing_info']
                    if 'chunk_info' in info:
                        chunk_info = info['chunk_info']
                        print(f"  Chunks: {chunk_info.get('total_chunks', 'unknown')}")
                        print(f"  Characters: {chunk_info.get('total_characters', 'unknown')}")
                        print(f"  Avg chunk size: {chunk_info.get('avg_chunk_size', 'unknown'):.0f}")
                
                print("  Saved as output/full_text_json_output.wav")
                return True
            else:
                print(f"✗ Full-text JSON generation failed: {data['message']}")
                return False
        else:
            print(f"✗ Full-text JSON generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Full-text JSON generation error: {e}")
        return False


def test_performance_comparison():
    """Compare performance between standard and full-text endpoints"""
    print("\nTesting performance comparison...")
    
    # Short text for standard endpoint
    short_text = "This is a short text for performance comparison testing."
    
    # Medium text that benefits from chunking
    medium_text = """
    This is a medium-length text designed to test the performance differences
    between the standard endpoint and the enhanced full-text endpoint.
    
    The full-text endpoint should show its advantages when processing longer
    texts that require intelligent chunking and parallel processing.
    
    This text is long enough to require multiple chunks but not so long
    that it becomes unwieldy for testing purposes.
    """
    
    results = {}
    
    try:
        # Test standard endpoint with short text
        import time
        start_time = time.time()
        response = requests.post(
            ENDPOINTS["generate_audio"],
            json={"text": short_text},
            timeout=30
        )
        if response.status_code == 200:
            results['standard_short'] = time.time() - start_time
            print(f"✓ Standard endpoint (short): {results['standard_short']:.2f}s")
        
        # Test full-text endpoint with medium text
        if ENDPOINTS["generate_full_text_audio"]:
            start_time = time.time()
            response = requests.post(
                ENDPOINTS["generate_full_text_audio"],
                json={
                    "text": medium_text.strip(),
                    "max_chunk_size": 300
                },
                timeout=60
            )
            if response.status_code == 200:
                results['fulltext_medium'] = time.time() - start_time
                chunks = response.headers.get('X-Chunks-Processed', 'unknown')
                print(f"✓ Full-text endpoint (medium, {chunks} chunks): {results['fulltext_medium']:.2f}s")
        
        # Summary
        if results:
            print("  Performance comparison complete!")
            return True
        else:
            print("  Could not complete performance comparison")
            return False
            
    except Exception as e:
        print(f"✗ Performance comparison error: {e}")
        return False

def main():
    """Run all tests"""
    print("Enhanced Chatterbox TTS API Test Suite")
    print("=" * 50)
    
    # Check if required endpoints are configured
    missing_endpoints = [name for name, url in ENDPOINTS.items() if not url]
    if missing_endpoints:
        print("⚠ Warning: Some endpoints not configured:")
        for endpoint in missing_endpoints:
            print(f"   {endpoint}")
        print("   Set environment variables in .env file")
        print()
    
    tests = [
        test_health_check,
        test_basic_generation,
        test_json_generation,
        test_voice_cloning,
        test_file_upload,
        test_legacy_endpoint,
        test_full_text_generation,
        test_performance_comparison
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"✓ {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("\nGenerated files in output/ directory:")
        output_dir = Path("output")
        if output_dir.exists():
            for file in output_dir.glob("*.wav"):
                size_kb = file.stat().st_size / 1024
                print(f"   {file.name} ({size_kb:.1f} KB)")
    else:
        print("⚠ Some tests failed - check your Modal deployment")
        
    print(f"\nAPI Endpoints tested:")
    for name, url in ENDPOINTS.items():
        status = "✓" if url else "✗"
        print(f"   {status} {name}: {url or 'Not configured'}")


def create_sample_env_file():
    """Create a sample .env file with endpoint placeholders"""
    env_content = """# Enhanced Chatterbox TTS API Endpoints
# Replace YOUR-MODAL-ENDPOINT with your actual Modal deployment URL

HEALTH_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/health
GENERATE_AUDIO_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate_audio
GENERATE_JSON_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate_json
GENERATE_WITH_FILE_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate_with_file
GENERATE_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate

# New enhanced endpoints
FULL_TEXT_TTS_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate_full_text_audio
FULL_TEXT_JSON_ENDPOINT=https://YOUR-MODAL-ENDPOINT.modal.run/generate_full_text_json
"""
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_content)
        print("Created sample .env file - please update with your actual endpoints")


if __name__ == "__main__":
    # Create sample .env if it doesn't exist
    create_sample_env_file()
    main()
