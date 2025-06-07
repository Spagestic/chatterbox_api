import os

def get_generate_audio_endpoint():
    return os.getenv("GENERATE_AUDIO_ENDPOINT", "YOUR-MODAL-ENDPOINT-URL/generate_audio")

def get_generate_with_file_endpoint():
    return os.getenv("GENERATE_WITH_FILE_ENDPOINT", "YOUR-MODAL-ENDPOINT-URL/generate_with_file")
