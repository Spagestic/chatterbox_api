def generate_tts_audio(text_input: str, audio_prompt_input, progress=None):
    from .tts_api_config import get_generate_audio_endpoint, get_generate_with_file_endpoint
    from .tts_api_requests import send_text_request, send_voice_clone_request
    from .audio_file_utils import download_and_read_audio
    import gradio as gr
    
    if not text_input or len(text_input.strip()) == 0:
        raise gr.Error("Please enter some text to synthesize.")
    if len(text_input) > 1000:
        raise gr.Error("Text is too long. Maximum 1000 characters allowed.")
    if progress: progress(0.1, desc="Preparing request...")
    try:
        if audio_prompt_input is None:
            if progress: progress(0.3, desc="Sending request to API...")
            endpoint = get_generate_audio_endpoint()
            response = send_text_request(text_input, endpoint, progress)
            if progress: progress(0.6, desc="Streaming audio response...")
            sample_rate, audio_data = download_and_read_audio(response, progress, 0.6, 0.9, "Downloading audio...")
            if progress: progress(1.0, desc="Complete!")
            return (sample_rate, audio_data)
        else:
            if progress: progress(0.3, desc="Preparing voice prompt...")
            endpoint = get_generate_with_file_endpoint()
            if progress: progress(0.5, desc="Sending request with voice cloning...")
            response = send_voice_clone_request(text_input, audio_prompt_input, endpoint, progress)
            if progress: progress(0.8, desc="Streaming cloned voice response...")
            sample_rate, audio_data = download_and_read_audio(response, progress, 0.8, 0.95, "Downloading cloned audio...")
            if progress: progress(1.0, desc="Voice cloning complete!")
            return (sample_rate, audio_data)
    except Exception as e:
        if isinstance(e, gr.Error):
            raise
        import requests
        if isinstance(e, requests.exceptions.Timeout):
            raise gr.Error("Request timed out. The API might be under heavy load. Please try again.")
        elif isinstance(e, requests.exceptions.ConnectionError):
            raise gr.Error("Unable to connect to the API. Please check if the endpoint URL is correct.")
        else:
            raise gr.Error(f"Error generating audio: {str(e)}")