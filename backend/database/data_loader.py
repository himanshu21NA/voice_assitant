import psycopg2
import os
import json
from utils.logging import Logger

logger = Logger(__name__)

def load_latest_dataset():
    """Load the latest dataset from database"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL not set")
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT content, created_at
            FROM scraped_data
            WHERE category = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, ("stevenscreek",))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            raise RuntimeError("No dataset found in DB")
        
        content, timestamp = row
        logger.info(f"Dataset loaded successfully, updated at {timestamp}")
        return content
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise