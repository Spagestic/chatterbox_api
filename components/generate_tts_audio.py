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
                timeout=60
            )
            if response.status_code != 200:
                raise gr.Error(f"API Error: {response.status_code} - {response.text}")
            if progress: progress(0.8, desc="Processing audio response...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
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
                timeout=120
            )
            if response.status_code != 200:
                raise gr.Error(f"API Error: {response.status_code} - {response.text}")
            if progress: progress(0.8, desc="Processing cloned voice response...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(response.content)
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