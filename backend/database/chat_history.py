import psycopg2
import os
import uuid
from typing import List, Dict, Optional
from utils.logging import Logger

logger = Logger(__name__)

def ensure_chat_history_table_exists():
    """Check if chat_history table exists, create it if it doesn't"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set, cannot create chat_history table")
            return False
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'chat_history'
            );
        """)
        
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            logger.info("chat_history table does not exist, creating it...")
            
            # Create the table
            cur.execute("""
                CREATE TABLE chat_history (
                    id SERIAL PRIMARY KEY,
                    session_id UUID NOT NULL,
                    user_query TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for better performance
            cur.execute("""
                CREATE INDEX idx_chat_history_session_id ON chat_history(session_id);
            """)
            
            # Create index on created_at for time-based queries
            cur.execute("""
                CREATE INDEX idx_chat_history_created_at ON chat_history(created_at);
            """)
            
            conn.commit()
            logger.info("chat_history table created successfully with indexes")
        else:
            logger.info("chat_history table already exists")
            
            # Check if session_id column exists (for backwards compatibility)
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'chat_history' 
                AND column_name = 'session_id';
            """)
            
            session_id_exists = cur.fetchone()
            
            if not session_id_exists:
                logger.info("session_id column missing, adding it...")
                cur.execute("""
                    ALTER TABLE chat_history 
                    ADD COLUMN session_id UUID;
                """)
                
                cur.execute("""
                    CREATE INDEX idx_chat_history_session_id ON chat_history(session_id);
                """)
                
                conn.commit()
                logger.info("session_id column added successfully")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to ensure chat_history table exists: {e}")
        return False

async def create_new_session() -> str:
    """Create a new session ID"""
    # Ensure table exists before creating session
    ensure_chat_history_table_exists()
    
    session_id = str(uuid.uuid4())
    logger.info(f"Created new session ID: {session_id}")
    return session_id

def get_recent_chat_history(session_id: str, limit: int = 5) -> List[Dict]:
    """Get recent chat history for a specific session"""
    try:
        # Ensure table exists
        if not ensure_chat_history_table_exists():
            logger.warning("Could not ensure chat_history table exists")
            return []
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set, no chat history available")
            return []
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT user_query, assistant_response, created_at
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (session_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Return in chronological order (oldest first)
        chat_history = []
        for row in reversed(rows):
            chat_history.append({
                "user_query": row[0],
                "assistant_response": row[1],
                "created_at": row[2]
            })
        
        logger.info(f"Retrieved {len(chat_history)} chat history entries for session {session_id}")
        return chat_history
        
    except Exception as e:
        logger.error(f"Failed to get chat history for session {session_id}: {e}")
        return []

def save_chat_history(session_id: str, user_query: str, assistant_response: str):
    """Save chat interaction to database with session ID"""
    try:
        # Ensure table exists
        if not ensure_chat_history_table_exists():
            logger.warning("Could not ensure chat_history table exists, skipping save")
            return
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set, skipping chat history save")
            return
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_history (session_id, user_query, assistant_response)
            VALUES (%s, %s, %s)
        """, (session_id, user_query, assistant_response))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Chat history saved successfully for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save chat history for session {session_id}: {e}")

def format_chat_history(chat_history: List[Dict]) -> str:
    """Format chat history for prompt inclusion"""
    if not chat_history:
        return ""
    
    formatted = "Previous conversation:\n"
    for entry in chat_history:
        formatted += f"User: {entry['user_query']}\n"
        formatted += f"Assistant: {entry['assistant_response']}\n\n"
    
    return formatted

def format_chat_history_for_enhancement(chat_history: List[Dict]) -> str:
    """Format chat history specifically for query enhancement"""
    if not chat_history:
        return ""
    
    formatted = "Previous conversation context:\n"
    for entry in chat_history:
        formatted += f"Q: {entry['user_query']}\nA: {entry['assistant_response']}\n\n"
    
    return formatted

def cleanup_old_sessions(days_old: int = 30):
    """Clean up chat history older than specified days (optional maintenance function)"""
    try:
        if not ensure_chat_history_table_exists():
            logger.warning("Could not ensure chat_history table exists")
            return
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set, cannot cleanup old sessions")
            return
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM chat_history 
            WHERE created_at < NOW() - INTERVAL '%s days'
        """, (days_old,))
        
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old chat history records older than {days_old} days")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old sessions: {e}")