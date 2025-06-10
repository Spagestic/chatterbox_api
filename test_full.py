
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


def run_tests():
    test_full_text_generation()
    test_full_text_json()
    
if __name__ == "__main__":
    print("Running full-text TTS tests...")
    run_tests()
    print("All tests completed.")
