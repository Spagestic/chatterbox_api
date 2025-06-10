"""Audio processing utilities for the TTS API."""

import re
from typing import List


class AudioConcatenator:
    """Server-side audio concatenation with GPU acceleration."""
    
    def __init__(self, silence_duration: float = 0.5, fade_duration: float = 0.1):
        """
        Initialize the audio concatenator.
        
        Args:
            silence_duration: Duration of silence between chunks (seconds)
            fade_duration: Duration of fade in/out effects (seconds)
        """
        self.silence_duration = silence_duration
        self.fade_duration = fade_duration
    
    def concatenate_audio_chunks(self, audio_chunks: List, sample_rate: int):
        """
        Concatenate multiple audio chunks into a single audio file.
        
        Args:
            audio_chunks: List of audio arrays
            sample_rate: Sample rate for the audio
            
        Returns:
            Concatenated audio array
        """
        if not audio_chunks:
            raise ValueError("No audio chunks to concatenate")
        
        if len(audio_chunks) == 1:
            # Handle single chunk case
            audio = audio_chunks[0]
            if isinstance(audio, tuple):
                return audio[0]  # Extract audio data from tuple
            return audio
        
        import numpy as np
        import torch
        
        # Normalize and prepare audio data
        normalized_chunks = []
        for i, audio_data in enumerate(audio_chunks):
            print(f"Processing chunk {i}: type={type(audio_data)}")
            
            # Handle tuple format (common from TTS models)
            if isinstance(audio_data, tuple):
                audio_data = audio_data[0]  # Extract audio array from tuple
                print(f"  Extracted from tuple: type={type(audio_data)}")
            
            # Convert torch tensor to numpy if needed
            if hasattr(audio_data, 'cpu'):  # It's a torch tensor
                audio_data = audio_data.cpu().numpy()
                print(f"  Converted from torch: shape={audio_data.shape}")
            
            # Convert to numpy array if needed
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
            
            print(f"  Final shape before processing: {audio_data.shape}")
            
            # Handle different audio shapes
            if audio_data.ndim == 1:
                # Already 1D, perfect
                normalized_audio = audio_data
            elif audio_data.ndim == 2:
                # Handle 2D audio - could be (channels, samples) or (samples, channels)
                if audio_data.shape[0] < audio_data.shape[1]:
                    # Likely (channels, samples) - take first channel
                    normalized_audio = audio_data[0, :]
                    print(f"  Used first channel from (C, L) format: {normalized_audio.shape}")
                else:
                    # Likely (samples, channels) - take first channel
                    normalized_audio = audio_data[:, 0]
                    print(f"  Used first channel from (L, C) format: {normalized_audio.shape}")
            else:
                # Flatten higher dimensional arrays
                normalized_audio = audio_data.flatten()
                print(f"  Flattened {audio_data.ndim}D array: {normalized_audio.shape}")
            
            # Ensure we have valid audio data
            if len(normalized_audio) == 0:
                print(f"  Warning: Empty audio chunk {i}")
                continue
            
            print(f"  Chunk {i} final length: {len(normalized_audio)} samples ({len(normalized_audio)/sample_rate:.2f}s)")
            
            # Normalize audio levels
            normalized_audio = self._normalize_audio(normalized_audio)
            
            # Apply fade effects
            normalized_audio = self._apply_fade_effects(normalized_audio, sample_rate)
            
            normalized_chunks.append(normalized_audio)
        
        if not normalized_chunks:
            raise ValueError("No valid audio chunks after processing")
        
        print(f"Successfully processed {len(normalized_chunks)} chunks")
        
        # Create silence segments
        silence_samples = int(self.silence_duration * sample_rate)
        silence = np.zeros(silence_samples, dtype=np.float32)
        print(f"Adding {silence_samples} silence samples ({self.silence_duration}s) between chunks")
        
        # Concatenate all chunks with silence in between
        concatenated_segments = []
        total_audio_length = 0
        
        for i, chunk in enumerate(normalized_chunks):
            concatenated_segments.append(chunk)
            total_audio_length += len(chunk)
            print(f"Added chunk {i}: {len(chunk)} samples")
            
            # Add silence between chunks (but not after the last chunk)
            if i < len(normalized_chunks) - 1:
                concatenated_segments.append(silence)
                total_audio_length += len(silence)
                print(f"Added silence: {len(silence)} samples")
        
        # Combine all segments
        final_audio = np.concatenate(concatenated_segments)
        print(f"Final concatenated audio: {len(final_audio)} samples ({len(final_audio)/sample_rate:.2f}s)")
        
        # Final normalization and cleanup
        final_audio = self._normalize_audio(final_audio)
        final_audio = self._remove_clicks_and_pops(final_audio)
        
        return final_audio

    def _normalize_audio(self, audio_data):
        """Normalize audio to prevent clipping."""
        import numpy as np
        
        # Convert to numpy array if it's not already
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data)
        
        # Ensure it's a 1D array
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()
        
        # Find the maximum absolute value
        max_val = np.max(np.abs(audio_data))
        
        if max_val == 0:
            return audio_data
        
        # Normalize to 95% of maximum to leave some headroom
        normalized = audio_data * (0.95 / max_val)
        
        return normalized.astype(np.float32)
    
    def _apply_fade_effects(self, audio_data, sample_rate: int):
        """Apply fade in and fade out effects to reduce pops and clicks."""
        import numpy as np
        
        fade_samples = int(self.fade_duration * sample_rate)
        
        if len(audio_data) < 2 * fade_samples:
            # If audio is too short for fade effects, return as-is
            return audio_data
        
        audio_with_fades = audio_data.copy()
        
        # Apply fade in
        fade_in = np.linspace(0, 1, fade_samples)
        audio_with_fades[:fade_samples] *= fade_in
        
        # Apply fade out
        fade_out = np.linspace(1, 0, fade_samples)
        audio_with_fades[-fade_samples:] *= fade_out
        
        return audio_with_fades
    
    def _remove_clicks_and_pops(self, audio_data):
        """Apply basic filtering to remove clicks and pops."""
        try:
            # Simple high-pass filter to remove DC offset and low-frequency artifacts
            from scipy import signal
            import numpy as np
            
            # Design a high-pass filter (removes frequencies below 80 Hz)
            # This helps remove some pops and clicks while preserving speech
            nyquist = 22050 / 2  # Assuming common sample rate
            low = 80 / nyquist
            b, a = signal.butter(4, low, btype='high')
            filtered_audio = signal.filtfilt(b, a, audio_data)
            return filtered_audio.astype(np.float32)
        except ImportError:
            # If scipy is not available, return original audio
            return audio_data