import logging
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from typing import List, Dict
from prompts import QUERY_ENHANCEMENT_PROMPT
# Initialize OpenAI client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logging.info("OpenAI client initialized in query enhancer")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client in query enhancer: {e}")


def enhance_query(current_query: str, chat_history: List[Dict]) -> str:
    """
    Enhance the user query using chat history context to create a standalone query
    """
    try:
        # If no chat history, return the original query
        if not chat_history:
            logging.info("No chat history available, returning original query")
            return current_query
        
        # Format chat history for enhancement
        chat_context = ""
        for entry in chat_history:
            chat_context += f"Q: {entry['user_query']}\nA: {entry['assistant_response']}\n\n"
        
        # If chat context is empty, return original query
        if not chat_context.strip():
            logging.info("Empty chat context, returning original query")
            return current_query
        
        # Create enhancement prompt
        enhancement_prompt = QUERY_ENHANCEMENT_PROMPT.format(
            chat_context=chat_context,
            current_query=current_query
        )
        
        logging.info("Enhancing query with chat history context")
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": enhancement_prompt}],
            temperature=0, 
            max_tokens=150,  
        )
        
        enhanced_query = response.choices[0].message.content.strip()
        
        # Fallback to original query if enhancement failed
        if not enhanced_query or len(enhanced_query) < 3:
            logging.warning("Query enhancement returned empty result, using original query")
            return current_query
        
        logging.info(f"Query enhanced from: '{current_query}' to: '{enhanced_query}'")
        return enhanced_query
        
    except Exception as e:
        logging.error(f"Failed to enhance query: {e}")
        # Return original query if enhancement fails
        return current_query