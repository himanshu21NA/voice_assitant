import json
import hashlib
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

import faiss
import numpy as np
# --- PROMPT ---
from prompt import GENERATION_PROMPT
from config import OPENAI_API_KEY, OPENAI_MODEL
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY is not set. Please set the environment variable.")
else:
    logging.info("OPENAI_API_KEY loaded successfully.")
# --- GENERATION FUNCTION ---
def generate_response(user_query: str, context: str = "") -> str:
    """
    Generate a response using the assistant prompt, user query, and optional context.
    """
    prompt = f"{GENERATION_PROMPT}\n\nContext: {context}\n\nUser: {user_query}\nAssistant:"
    logging.info(f"Calling OpenAI with prompt: {prompt[:100]}... (truncated)")
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0)
        logging.info("OpenAI response received successfully.")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        return "Error: Could not generate response."

# --- CONFIG ---
JSON_PATH = "stevenscreek_dataset.json"
EMBED_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logging.info("OpenAI client initialized.")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}")


# --- HELPERS ---
def normalize(text: str) -> str:
    return " ".join(text.lower().split())

def deduplicate_texts(texts: List[str], threshold: float = 0.9) -> List[str]:
    texts = [normalize(t) for t in texts if t.strip()]
    if not texts:
        return []

    # Exact deduplication
    unique = []
    hashes = set()
    for t in texts:
        h = hashlib.md5(t.encode()).hexdigest()
        if h not in hashes:
            unique.append(t)
            hashes.add(h)

    if len(unique) < 2:
        return unique

    try:
        # Near-duplicate filtering using cosine similarity
        vectorizer = TfidfVectorizer().fit_transform(unique)
        vectors = vectorizer.toarray()
        keep = [True] * len(unique)

        for i in range(len(unique)):
            if not keep[i]:
                continue
            if i + 1 >= len(unique):  # avoid empty slice
                break
            sims = cosine_similarity([vectors[i]], vectors[i+1:])[0]
            for j, sim in enumerate(sims, start=i+1):
                if sim > threshold:
                    keep[j] = False

        return [t for t, k in zip(unique, keep) if k]

    except Exception as e:
        print(f"[WARN] Dedup skipped due to: {e}")
        return unique


def chunk_text(text: str, max_words: int = 100) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def save_corpus(corpus, path="cleaned_corpus.json"):
    with open(path, "w") as f:
        json.dump(corpus, f, indent=2)

# --- Load corpus ---
def load_corpus(path="cleaned_corpus.json"):
    with open(path, "r") as f:
        return json.load(f)

def build_corpus(data: Dict) -> List[Dict]:
    corpus = []
    for section, entries in data.items():
        if isinstance(entries, list):
            if all(isinstance(e, str) for e in entries):
                cleaned = deduplicate_texts(entries)
                for idx, text in enumerate(cleaned):
                    for chunk in chunk_text(text):
                        corpus.append({
                            "section": section,
                            "chunk_id": f"{section}_{idx}",
                            "text": chunk
                        })
            elif all(isinstance(e, dict) for e in entries):  # structured inventory
                for e in entries:
                    text = f"{e.get('year','')} {e.get('make','')} {e.get('model','')}, Trim: {e.get('trim','')}, Price: {e.get('price','')}, Fuel Type: {e.get('fuel','')}, Description: {e.get('description','')}"
                    corpus.append({
                        "section": section,
                        "chunk_id": e.get("vin", ""),
                        "text": text,
                        "metadata": e
                    })

    return corpus

def embed_texts(texts: List[str], model: str = EMBED_MODEL) -> np.ndarray:
    embeddings = []
    for i in range(0, len(texts), 100):  # batch API calls
        batch = texts[i:i+500]
        resp = client.embeddings.create(model=model, input=batch)
        embeddings.extend([e.embedding for e in resp.data])
    return np.array(embeddings).astype("float32")

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def search(query: str, corpus: List[Dict], index, k: int = 5):
    q_emb = client.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding
    q_emb = np.array([q_emb]).astype("float32")
    D, I = index.search(q_emb, k)
    results = []
    for j, i in enumerate(I[0]):
        if i < len(corpus):
            results.append((corpus[i], float(D[0][j])))
        else:
            logging.warning(f"Index {i} out of bounds for corpus of size {len(corpus)}.")
    return results

# --- MAIN FUNCTION ---
def response(query:str):
    # Load JSON
    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    corpus = build_corpus(data)
    if not corpus:
        logging.error("Corpus is empty!")
        return "Error: No data available."

    save_corpus(corpus, path="cleaned_corpus.json")
    texts = [c["text"] for c in corpus]
    embeddings = embed_texts(texts)
    if embeddings.size == 0:
        logging.error("Embeddings are empty!")
        return "Error: No embeddings generated."

    index = build_faiss_index(embeddings)
    results = search(query, corpus, index, k=10)
    if not results:
        logging.error("No search results found!")
        return "Error: No relevant results found."
    for r in results:
        print("SECTION:", r[0]["section"])
        print("TEXT:", r[0]["text"])
        print("DISTANCE:", r[1])
        print("---")
    context = "\n".join([r[0]["text"] for r in results])
    response_text = generate_response(query, context)
    print("RESPONSE:", response_text)
    return response_text

# if __name__ == "__main__":
#     main()

