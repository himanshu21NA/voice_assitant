import numpy as np
import faiss
from typing import List
from openai import OpenAI
from config import OPENAI_API_KEY
from utils.logging import Logger

# Initialize logger
logger = Logger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI client initialized in embedder module")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client in embedder: {e}")

def embed_texts(texts: List[str], model: str = "text-embedding-3-small") -> np.ndarray:
    """Create embeddings for a list of texts"""
    try:
        embeddings = []
        for i in range(0, len(texts), 100):
            batch = texts[i:i+100]
            resp = client.embeddings.create(model=model, input=batch)
            embeddings.extend([e.embedding for e in resp.data])
            logger.debug(f"Processed batch {i//100 + 1}/{(len(texts)-1)//100 + 1}")
        
        result = np.array(embeddings).astype("float32")
        logger.info(f"Successfully embedded {len(texts)} texts with shape {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Failed to embed texts: {e}")
        raise

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Build FAISS index from embeddings"""
    try:
        dim = embeddings.shape[1]
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        index = faiss.IndexFlatIP(dim)  # Inner Product
        index.add(embeddings)
        
        logger.info(f"FAISS index built successfully with {embeddings.shape[0]} vectors of dimension {dim}")
        return index
    except Exception as e:
        logger.error(f"Failed to build FAISS index: {e}")
        raise