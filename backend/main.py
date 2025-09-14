from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag import stream_response
from database.chat_history import create_new_session, ensure_chat_history_table_exists
from utils.logging import Logger

app = FastAPI()
logger = Logger(__name__)

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure chat_history table exists on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("Starting up application...")
    ensure_chat_history_table_exists()
    logger.info("Application startup completed")

class ChatRequest(BaseModel):
    text: str
    session_id: str = None  # Optional, will create new if not provided

class SessionResponse(BaseModel):
    session_id: str

@app.post("/create_session", response_model=SessionResponse)
async def create_session():
    """Create a new chat session"""
    try:
        session_id = create_new_session()
        return SessionResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {e}")

@app.post("/process_text")
async def process_text(request: ChatRequest):
    """Process text with optional session management"""
    try:
        # Create new session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = create_new_session()
            logger.info(f"Created new session for request: {session_id}")
        
        return StreamingResponse(
            stream_response(request.text, session_id),
            media_type="text/plain",
            headers={"X-Session-ID": session_id}  # Return session ID in header
        )
    except Exception as e:
        logger.error(f"Error in /process_text/: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "RAG API is running"}