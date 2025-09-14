from utils.logging import Logger
import logging
from typing import List

logger = Logger(__name__)

def chunk_text(text: str, max_words: int = 250) -> List[str]:
    """Split text into chunks of specified word count"""
    try:
        words = text.split()
        chunks = [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]
        logger.debug(f"Text chunked into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to chunk text: {e}")
        return [text]  # Return original text if chunking fails