import json
import logging
from utils.logging import Logger

logger = Logger(__name__)

def normalize(text: str) -> str:
    """Normalize text by converting to lowercase and removing extra spaces"""
    return " ".join(text.lower().split())

def save_corpus(corpus, path="cleaned_corpus.json"):
    """Save corpus to JSON file"""
    try:
        with open(path, "w") as f:
            json.dump(corpus, f, indent=2)
        logger.info(f"Corpus saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save corpus: {e}")