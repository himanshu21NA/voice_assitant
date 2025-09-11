import json
import hashlib
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import faiss
import numpy as np
from config import OPENAI_API_KEY
# --- CONFIG ---
JSON_PATH = "stevenscreek_dataset.json"
EMBED_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"
client = OpenAI(api_key=OPENAI_API_KEY)


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
                    text = f"{e.get('year','')} {e.get('make','')} {e.get('model','')}, Trim: {e.get('trim','')}, Price: {e.get('price','')}, Mileage: {e.get('mileage','')}"
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
        batch = texts[i:i+100]
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
    return [(corpus[i], float(D[0][j])) for j, i in enumerate(I[0])]

# --- MAIN FUNCTION ---
def main():
    # Load JSON
    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    # Build cleaned corpus
    corpus = build_corpus(data)

    # Save cleaned corpus
    save_corpus(corpus, path="cleaned_corpus.json")
    # Embed
    texts = [c["text"] for c in corpus]
    embeddings = embed_texts(texts)

    # Build FAISS index
    index = build_faiss_index(embeddings)

    # Test RAG query
    results = search("I need to schedule a service appointment", corpus, index, k=3)
    for r in results:
        print("SECTION:", r[0]["section"])
        print("TEXT:", r[0]["text"])
        print("DISTANCE:", r[1])
        print("---")

if __name__ == "__main__":
    main()

# import json
# import hashlib
# from typing import List, Dict
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from openai import OpenAI
# import faiss
# import uuid
# import numpy as np
# from config import OPENAI_API_KEY
# import chromadb

# # --- CONFIG ---
# JSON_PATH = "stevenscreek_dataset.json"
# EMBED_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"
# client = OpenAI(api_key=OPENAI_API_KEY)

# # --- INIT CHROMA ---
# chroma_client = chromadb.Client()
# COLLECTION_NAME = "dealer_offers"

# # Delete old collection if it exists (prevents duplicate ID errors)
# try:
#     chroma_client.delete_collection(COLLECTION_NAME)
#     print(f"Deleted existing Chroma collection: {COLLECTION_NAME}")
# except Exception:
#     print(f"No existing Chroma collection named {COLLECTION_NAME}")

# collection = chroma_client.create_collection(COLLECTION_NAME)
# # --- FUNCTION: store corpus in chroma ---
# def store_corpus_in_chroma(corpus, model="text-embedding-3-small"):
#     texts = [c["text"] for c in corpus]
#     ids = [c["chunk_id"] for c in corpus]
#     metadatas = [{"section": c["section"]} for c in corpus]

#     # Generate embeddings
#     embeddings = []
#     for i in range(0, len(texts), 100):
#         batch = texts[i:i+100]
#         resp = client.embeddings.create(model=model, input=batch)
#         embeddings.extend([e.embedding for e in resp.data])

#     # Insert into Chroma
#     collection.add(
#         ids=ids,
#         documents=texts,
#         embeddings=embeddings,
#         metadatas=metadatas
#     )
#     return {"status": "stored", "count": len(corpus)}

# # --- CHROMA QUERY ---
# def query_chroma(question: str, n_results=3):
#     results = collection.query(query_texts=[question], n_results=n_results)
#     return {
#         "question": question,
#         "documents": results["documents"][0],
#         "metadatas": results["metadatas"][0]
#     }

# # --- HELPERS ---
# def normalize(text: str) -> str:
#     return " ".join(text.lower().split())

# def deduplicate_texts(texts: List[str], threshold: float = 0.9) -> List[str]:
#     texts = [normalize(t) for t in texts if t.strip()]
#     if not texts:
#         return []

#     # Exact deduplication
#     unique = []
#     hashes = set()
#     for t in texts:
#         h = hashlib.md5(t.encode()).hexdigest()
#         if h not in hashes:
#             unique.append(t)
#             hashes.add(h)

#     if len(unique) < 2:
#         return unique

#     try:
#         # Near-duplicate filtering using cosine similarity
#         vectorizer = TfidfVectorizer().fit_transform(unique)
#         vectors = vectorizer.toarray()
#         keep = [True] * len(unique)

#         for i in range(len(unique)):
#             if not keep[i]:
#                 continue
#             if i + 1 >= len(unique):  # avoid empty slice
#                 break
#             sims = cosine_similarity([vectors[i]], vectors[i+1:])[0]
#             for j, sim in enumerate(sims, start=i+1):
#                 if sim > threshold:
#                     keep[j] = False

#         return [t for t, k in zip(unique, keep) if k]

#     except Exception as e:
#         print(f"[WARN] Dedup skipped due to: {e}")
#         return unique

# def chunk_text(text: str, max_words: int = 100) -> List[str]:
#     words = text.split()
#     return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# def save_corpus(corpus, path="cleaned_corpus.json"):
#     with open(path, "w") as f:
#         json.dump(corpus, f, indent=2)

# def load_corpus(path="cleaned_corpus.json"):
#     with open(path, "r") as f:
#         return json.load(f)

# def build_corpus(data: Dict) -> List[Dict]:
#     corpus = []
#     for section, entries in data.items():
#         if isinstance(entries, list):
#             if all(isinstance(e, str) for e in entries):
#                 cleaned = deduplicate_texts(entries)
#                 for idx, text in enumerate(cleaned):
#                     for chunk_idx, chunk in enumerate(chunk_text(text)):
#                         corpus.append({
#                             "section": section,
#                             "chunk_id": f"{section}_{idx}_{chunk_idx}_{uuid.uuid4().hex[:8]}",
#                             "text": chunk
#                         })
#             elif all(isinstance(e, dict) for e in entries):  # structured inventory
#                 for e in entries:
#                     text = f"{e.get('year','')} {e.get('make','')} {e.get('model','')}, Trim: {e.get('trim','')}, Price: {e.get('price','')}, Mileage: {e.get('mileage','')}"
#                     corpus.append({
#                         "section": section,
#                         "chunk_id": f"{e.get('vin','')}_{uuid.uuid4().hex[:8]}",
#                         "text": text,
#                         "metadata": e
#                     })
#     return corpus


# def embed_texts(texts: List[str], model: str = EMBED_MODEL) -> np.ndarray:
#     embeddings = []
#     for i in range(0, len(texts), 100):  # batch API calls
#         batch = texts[i:i+100]
#         resp = client.embeddings.create(model=model, input=batch)
#         embeddings.extend([e.embedding for e in resp.data])
#     return np.array(embeddings).astype("float32")

# def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
#     dim = embeddings.shape[1]
#     index = faiss.IndexFlatL2(dim)
#     index.add(embeddings)
#     return index

# def search(query: str, corpus: List[Dict], index, k: int = 5):
#     q_emb = client.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding
#     q_emb = np.array([q_emb]).astype("float32")
#     D, I = index.search(q_emb, k)
#     return [(corpus[i], float(D[0][j])) for j, i in enumerate(I[0])]

# # --- MAIN FUNCTION ---
# def main():
#     # Load JSON
#     with open(JSON_PATH, "r") as f:
#         data = json.load(f)

#     # Build cleaned corpus
#     corpus = build_corpus(data)

#     # Save cleaned corpus
#     save_corpus(corpus, path="cleaned_corpus.json")

#     # Store in Chroma
#     store_result = store_corpus_in_chroma(corpus)
#     print("Chroma Store:", store_result)

#     # Embed for FAISS
#     texts = [c["text"] for c in corpus]
#     embeddings = embed_texts(texts)

#     # Build FAISS index
#     index = build_faiss_index(embeddings)

#     # --- Test FAISS query ---
#     print("\nFAISS Results:")
#     results = search("I need to schedule a service appointment", corpus, index, k=3)
#     for r in results:
#         print("SECTION:", r[0]["section"])
#         print("TEXT:", r[0]["text"])
#         print("DISTANCE:", r[1])
#         print("---")

#     # --- Test Chroma query ---
#     print("\nChroma Results:")
#     c_results = query_chroma("I need to schedule a service appointment", n_results=3)
#     for doc, meta in zip(c_results["documents"], c_results["metadatas"]):
#         print("SECTION:", meta["section"])
#         print("TEXT:", doc)
#         print("---")

# if __name__ == "__main__":
#     main()

