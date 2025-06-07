import requests
import gradio as gr

def send_text_request(text_input, endpoint, progress=None):
    payload = {"text": text_input}
    response = requests.post(
        endpoint,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120,
        stream=True
    )
    if response.status_code != 200:
        raise gr.Error(f"API Error: {response.status_code} - {response.text}")
    return response

def send_voice_clone_request(text_input, audio_prompt_input, endpoint, progress=None):
    files = {'text': (None, text_input)}
    with open(audio_prompt_input, 'rb') as f:
        audio_content = f.read()
    files['voice_prompt'] = ('voice_prompt.wav', audio_content, 'audio/wav')
    response = requests.post(
        endpoint,
        files=files,
        timeout=180,
        stream=True
    )
    if response.status_code != 200:
        raise gr.Error(f"API Error: {response.status_code} - {response.text}")
    return response
