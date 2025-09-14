import numpy as np
from typing import List, Dict, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY
from utils.logging import Logger

# Initialize logger
logger = Logger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI client initialized in search module")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client in search: {e}")

def search(query: str, corpus: List[Dict], index, k: int = 5) -> List[Tuple[Dict, float]]:
    """Search for similar documents using FAISS index"""
    try:
        q_emb = client.embeddings.create(model="text-embedding-3-small", input=[query]).data[0].embedding
        logger.debug("Query embedded successfully")
        
        q_emb = np.array([q_emb]).astype("float32")
        logger.debug("Query converted to numpy array")
        
        D, I = index.search(q_emb, k)
        logger.debug("FAISS search completed")

        results = []
        for j, i in enumerate(I[0]):
            if i < len(corpus):
                results.append((corpus[i], float(D[0][j])))
                logger.info(f"(score: {D[0][j]})")
        logger.info(f"Search completed with {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Failed to perform search: {e}")
        return []