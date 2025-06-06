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
    "generate": os.getenv("GENERATE_ENDPOINT")
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

def main():
    """Run all tests"""
    print("Enhanced Chatterbox TTS API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_basic_generation,
        test_json_generation,
        test_voice_cloning,
        test_file_upload,
        test_legacy_endpoint
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
    else:
        print("⚠ Some tests failed - check your Modal deployment")

if __name__ == "__main__":
    main()
