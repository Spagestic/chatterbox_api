def generate_tts_audio(text_input: str, audio_prompt_input, progress=None):
    import os
    import requests
    import tempfile
    import soundfile as sf
    import numpy as np
    import gradio as gr
    
    GENERATE_AUDIO_ENDPOINT = os.getenv("GENERATE_AUDIO_ENDPOINT", "YOUR-MODAL-ENDPOINT-URL/generate_audio")
    GENERATE_WITH_FILE_ENDPOINT = os.getenv("GENERATE_WITH_FILE_ENDPOINT", "YOUR-MODAL-ENDPOINT-URL/generate_with_file")
    
    if not text_input or len(text_input.strip()) == 0:
        raise gr.Error("Please enter some text to synthesize.")
    if len(text_input) > 1000:
        raise gr.Error("Text is too long. Maximum 1000 characters allowed.")
    
    if progress: progress(0.1, desc="Preparing request...")
    
    try:
        if audio_prompt_input is None:
            if progress: progress(0.3, desc="Sending request to API...")
            payload = {"text": text_input}
            response = requests.post(
                GENERATE_AUDIO_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120,
                stream=True
            )
            if response.status_code != 200:
                raise gr.Error(f"API Error: {response.status_code} - {response.text}")
            
            if progress: progress(0.6, desc="Streaming audio response...")
            
            # Get content length if available for progress tracking
            content_length = response.headers.get('content-length')
            if content_length:
                content_length = int(content_length)
            
            bytes_downloaded = 0
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        bytes_downloaded += len(chunk)
                        
                        # Update progress based on bytes downloaded
                        if content_length and progress:
                            download_progress = min(0.3, (bytes_downloaded / content_length) * 0.3)
                            progress(0.6 + download_progress, desc=f"Downloading audio... ({bytes_downloaded // 1024}KB)")
                        elif progress:
                            # If no content length, just show bytes downloaded
                            progress(0.6, desc=f"Downloading audio... ({bytes_downloaded // 1024}KB)")
                            
                temp_path = temp_file.name
                
            if progress: progress(0.9, desc="Processing audio...")
            audio_data, sample_rate = sf.read(temp_path)
            os.unlink(temp_path)
            if progress: progress(1.0, desc="Complete!")
            return (sample_rate, audio_data)
            
        else:
            if progress: progress(0.3, desc="Preparing voice prompt...")
            files = {'text': (None, text_input)}
            with open(audio_prompt_input, 'rb') as f:
                audio_content = f.read()
            files['voice_prompt'] = ('voice_prompt.wav', audio_content, 'audio/wav')
            
            if progress: progress(0.5, desc="Sending request with voice cloning...")
            response = requests.post(
                GENERATE_WITH_FILE_ENDPOINT,
                files=files,
                timeout=180,
                stream=True
            )
            if response.status_code != 200:
                raise gr.Error(f"API Error: {response.status_code} - {response.text}")
            
            if progress: progress(0.8, desc="Streaming cloned voice response...")
            
            # Get content length if available for progress tracking
            content_length = response.headers.get('content-length')
            if content_length:
                content_length = int(content_length)
            
            bytes_downloaded = 0
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        bytes_downloaded += len(chunk)
                        
                        # Update progress based on bytes downloaded for voice cloning
                        if content_length and progress:
                            download_progress = min(0.15, (bytes_downloaded / content_length) * 0.15)
                            progress(0.8 + download_progress, desc=f"Downloading cloned audio... ({bytes_downloaded // 1024}KB)")
                        elif progress:
                            progress(0.8, desc=f"Downloading cloned audio... ({bytes_downloaded // 1024}KB)")
                            
                temp_path = temp_file.name
                
            audio_data, sample_rate = sf.read(temp_path)
            os.unlink(temp_path)
            if progress: progress(1.0, desc="Voice cloning complete!")
            return (sample_rate, audio_data)
            
    except requests.exceptions.Timeout:
        raise gr.Error("Request timed out. The API might be under heavy load. Please try again.")
    except requests.exceptions.ConnectionError:
        raise gr.Error("Unable to connect to the API. Please check if the endpoint URL is correct.")
    except Exception as e:
        raise gr.Error(f"Error generating audio: {str(e)}")