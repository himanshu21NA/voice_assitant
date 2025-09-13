from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
from rag import stream_response

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

@app.post("/process_text/")
async def process_text(text: str):
    try:
        return StreamingResponse(
            stream_response(text),
            media_type="text/plain"
        )
    except Exception as e:
        logging.error(f"Error in /process_text/: {e}")
        return {"response_text": f"Error: {e}"}

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import logging

# # Local imports
# from rag import response

# # ---------------- APP INIT ----------------
# app = FastAPI()

# # Allow only your frontend domain
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # change to your frontend URL
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Logging config
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# # ---------------- API ENDPOINTS ----------------
# @app.post("/process_text/")
# async def process_text(text: str):
#     """Takes text, generates RAG response + TTS audio."""
#     try:
#         response_text = response(text) or "Sorry, I could not generate a response."
#         return {"response_text": response_text}
#     except Exception as e:
#         logging.error(f"Error in /process_text/: {e}")
#         return {"response_text": "Error: Could not process request.", "audio_file": None}
