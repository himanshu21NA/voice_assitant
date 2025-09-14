import logging
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import GENERATION_PROMPT

# Local imports
from database.chat_history import get_recent_chat_history, save_chat_history, format_chat_history
from database.data_loader import load_latest_dataset
from processing.corpus_builder import build_corpus
from processing.query_enhancer import enhance_query
from embedding.embedder import embed_texts, build_faiss_index
from embedding.search import search
from utils.logging import Logger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = Logger(__name__)

if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY is not set. Please set the environment variable.")
else:
    logging.info("OPENAI_API_KEY loaded successfully.")

# --- OpenAI client ---
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logging.info("OpenAI client initialized.")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}")

# --- STREAMING RESPONSE ---
def stream_response(user_query: str, session_id: str):
    """Main function to handle user queries with streaming response and session management"""
    try:
        # Get recent chat history for this session
        chat_history = get_recent_chat_history(session_id, limit=5)
        logging.info(f"Retrieved {len(chat_history)} chat history entries for session {session_id}")
        
        # Enhance query using chat history
        enhanced_query = enhance_query(user_query, chat_history)
        logging.info(f"Using enhanced query for search: '{enhanced_query}'")
        
        data = load_latest_dataset()
        logging.info("Dataset loaded successfully")
        
        corpus = build_corpus(data)
        logging.info(f"Corpus built with {len(corpus)} entries")
        
        texts = [c["text"] for c in corpus]
        logging.debug("Texts extracted from corpus")
        
        embeddings = embed_texts(texts)
        logging.info("Text embeddings created successfully")
        
        index = build_faiss_index(embeddings)
        logging.info("FAISS index built successfully")
        
        # Use enhanced query for search
        results = search(enhanced_query, corpus, index, k=10)
        logging.info(f"Search completed with {len(results)} results using enhanced query")
        
        context = "\n".join([r[0]["text"] for r in results])

        # Format chat history for the prompt (using original formatting)
        chat_context = format_chat_history(chat_history)
        
        # Build prompt with chat history (use original user query in prompt, not enhanced)
        prompt = f"{GENERATION_PROMPT}\n\n{chat_context}Context: {context}\n\nUser: {user_query}\nAssistant:"

        # Collect the full response for saving to chat history
        full_response = ""
        
        def token_generator():
            nonlocal full_response
            try:
                logging.info("Starting OpenAI streaming response")
                stream = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    stream=True,
                )
                
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        full_response += delta.content
                        yield delta.content
                
                # Save to chat history after streaming is complete (use original query)
                if full_response.strip():
                    save_chat_history(session_id, user_query, full_response)
                    logging.info(f"Response streaming completed and saved to chat history for session {session_id}")
                    
            except Exception as e:
                error_msg = f"[ERROR] {e}"
                logging.error(f"Error during streaming response: {e}")
                full_response = error_msg
                save_chat_history(session_id, user_query, error_msg)
                yield error_msg

        return token_generator()
        
    except Exception as e:
        logging.error(f"Error in stream_response: {e}")
        def error_generator():
            error_msg = f"[ERROR] Failed to process request: {e}"
            save_chat_history(session_id, user_query, error_msg)
            yield error_msg
        return error_generator()