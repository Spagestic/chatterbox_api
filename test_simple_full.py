#!/usr/bin/env python3
"""
Simple test for the full-text TTS endpoint to debug timeout issues.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_full_text():
    """Test with a very short text to isolate the timeout issue."""
    endpoint = os.getenv("GENERATE_FULL_TEXT_AUDIO_ENDPOINT")
    
    if not endpoint:
        print("❌ GENERATE_FULL_TEXT_AUDIO_ENDPOINT not found in environment")
        return False
        
    print(f"Testing endpoint: {endpoint}")
    
    # Very short text to minimize processing time
    test_text = "Hello world. This is a simple test."
    
    payload = {
        "text": test_text,
        "max_chunk_size": 800,  # Default values
        "silence_duration": 0.5,
        "fade_duration": 0.1,
        "overlap_sentences": 0
    }
    
    print(f"Sending request with {len(test_text)} characters...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=60,  # 1 minute timeout
            stream=True  # Enable streaming to handle large responses
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Save the audio file
            os.makedirs("output", exist_ok=True)
            with open("output/simple_full_text_test.wav", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            duration = response.headers.get('X-Audio-Duration', 'unknown')
            chunks = response.headers.get('X-Chunks-Processed', 'unknown')
            characters = response.headers.get('X-Total-Characters', 'unknown')
            
            print("✅ Success!")
            print(f"   Duration: {duration}s")
            print(f"   Chunks: {chunks}")
            print(f"   Characters: {characters}")
            print("   Saved as: output/simple_full_text_test.wav")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Running simple full-text TTS test...")
    success = test_simple_full_text()
    exit(0 if success else 1)
