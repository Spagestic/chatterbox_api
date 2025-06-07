import tempfile
import soundfile as sf
import os

def download_and_read_audio(response, progress=None, progress_start=0.6, progress_end=0.9, desc_prefix="Downloading audio..."):
    content_length = response.headers.get('content-length')
    if content_length:
        content_length = int(content_length)
    bytes_downloaded = 0
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                bytes_downloaded += len(chunk)
                if content_length and progress:
                    download_progress = min(progress_end - progress_start, (bytes_downloaded / content_length) * (progress_end - progress_start))
                    progress(progress_start + download_progress, desc=f"{desc_prefix} ({bytes_downloaded // 1024}KB)")
                elif progress:
                    progress(progress_start, desc=f"{desc_prefix} ({bytes_downloaded // 1024}KB)")
        temp_path = temp_file.name
    audio_data, sample_rate = sf.read(temp_path)
    os.unlink(temp_path)
    return sample_rate, audio_data
