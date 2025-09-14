from typing import Dict, List
from .text_processor import chunk_text
from utils.logging import Logger

logger = Logger(__name__)

def build_corpus(data: Dict) -> List[Dict]:
    """Build corpus from loaded data"""
    try:
        corpus = []
        for section, entries in data.items():
            if isinstance(entries, list):
                if all(isinstance(e, str) for e in entries):
                    for idx, text in enumerate(entries):
                        for chunk in chunk_text(text):
                            corpus.append({
                                "section": section,
                                "chunk_id": f"{section}_{idx}",
                                "text": chunk
                            })
                elif all(isinstance(e, dict) for e in entries):
                    for e in entries:
                        text = f"{e.get('year','')} {e.get('make','')} {e.get('model','')}, Trim: {e.get('trim','')}, Price: {e.get('price','')}, Fuel Type: {e.get('fuel','')}, Description: {e.get('description','')}"
                        corpus.append({
                            "section": section,
                            "chunk_id": e.get("vin", ""),
                            "text": text,
                            "metadata": e
                        })
        logger.info(f"Corpus built successfully with {len(corpus)} entries")
        return corpus
    except Exception as e:
        logger.error(f"Failed to build corpus: {e}")
        return []