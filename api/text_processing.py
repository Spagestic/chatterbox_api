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
