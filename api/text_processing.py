"""Text processing utilities for the TTS API."""

import re
from typing import List


class TextChunker:
    """Server-side text chunking for optimal GPU processing."""
    
    def __init__(self, max_chunk_size: int = 800, overlap_sentences: int = 0):
        """
        Initialize the text chunker.
        
        Args:
            max_chunk_size: Maximum number of characters per chunk
            overlap_sentences: Number of sentences to overlap between chunks for continuity
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Break text into smaller chunks based on paragraphs and sentence boundaries.
        
        Args:
            text: The input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = text.strip()
        
        # If text is within the limit, return as single chunk
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        
        # First, try to split by paragraphs
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) + 1 > self.max_chunk_size:
                # If we have content in current chunk, save it
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If the paragraph itself is too long, split it by sentences
                if len(paragraph) > self.max_chunk_size:
                    sentence_chunks = self._split_paragraph_into_sentences(paragraph)
                    for sentence_chunk in sentence_chunks:
                        if len(current_chunk) + len(sentence_chunk) + 1 > self.max_chunk_size:
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence_chunk
                        else:
                            if current_chunk:
                                current_chunk += " " + sentence_chunk
                            else:
                                current_chunk = sentence_chunk
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add any remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Apply overlap if specified
        if self.overlap_sentences > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\s*\n|(?:\n\s*){2,}', text)
        # Filter out empty paragraphs and strip whitespace
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_paragraph_into_sentences(self, paragraph: str) -> List[str]:
        """Split a long paragraph into sentence-based chunks."""
        # Split by sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If a single sentence is longer than max_chunk_size, we need to force-split it
            if len(sentence) > self.max_chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Force-split the long sentence into smaller pieces
                while len(sentence) > self.max_chunk_size:
                    # Find a good breaking point (prefer spaces)
                    break_point = self.max_chunk_size
                    if ' ' in sentence[:self.max_chunk_size]:
                        # Find the last space within the limit
                        break_point = sentence[:self.max_chunk_size].rfind(' ')
                    
                    chunk_part = sentence[:break_point]
                    chunks.append(chunk_part)
                    sentence = sentence[break_point:].strip()
                
                # Add the remaining part of the sentence
                if sentence:
                    current_chunk = sentence
                    
            elif len(current_chunk) + len(sentence) + 1 > self.max_chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add sentence overlap between chunks for better continuity."""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk stays the same
        
        for i in range(1, len(chunks)):
            # Get last few sentences from previous chunk
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            prev_sentences = re.split(r'(?<=[.!?])\s+', prev_chunk)
            overlap_text = " ".join(prev_sentences[-self.overlap_sentences:]) if len(prev_sentences) > self.overlap_sentences else ""
            
            if overlap_text:
                overlapped_chunk = overlap_text + " " + current_chunk
            else:
                overlapped_chunk = current_chunk
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def get_chunk_info(self, chunks: List[str]) -> dict:
        """Get information about the chunks."""
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(len(chunk) for chunk in chunks),
            "avg_chunk_size": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
            "max_chunk_size": max(len(chunk) for chunk in chunks) if chunks else 0,
            "min_chunk_size": min(len(chunk) for chunk in chunks) if chunks else 0
        }


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
        
        # Normalize and prepare audio data
        normalized_chunks = []
        for audio_data in audio_chunks:
            # Handle tuple format (common from TTS models)
            if isinstance(audio_data, tuple):
                audio_data = audio_data[0]  # Extract audio array from tuple
            
            # Convert to numpy array if needed
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
            
            # Ensure audio data is in the correct format
            if audio_data.ndim == 1:
                normalized_audio = audio_data
            elif audio_data.ndim == 2:
                # If stereo, take first channel
                normalized_audio = audio_data[:, 0] if audio_data.shape[1] > 0 else audio_data.flatten()
            else:
                normalized_audio = audio_data.flatten()
            
            # Normalize audio levels
            normalized_audio = self._normalize_audio(normalized_audio)
            
            # Apply fade effects
            normalized_audio = self._apply_fade_effects(normalized_audio, sample_rate)
            
            normalized_chunks.append(normalized_audio)
        
        # Create silence segments
        silence_samples = int(self.silence_duration * sample_rate)
        silence = np.zeros(silence_samples, dtype=np.float32)
        
        # Concatenate all chunks with silence in between
        concatenated_segments = []
        for i, chunk in enumerate(normalized_chunks):
            concatenated_segments.append(chunk)
            
            # Add silence between chunks (but not after the last chunk)
            if i < len(normalized_chunks) - 1:
                concatenated_segments.append(silence)
        
        # Combine all segments
        final_audio = np.concatenate(concatenated_segments)
        
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
