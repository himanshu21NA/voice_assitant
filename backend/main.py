from fastapi import FastAPI
from data import run_scraper
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pyttsx3
import uuid
import os

# RAG imports
from rag import response
import logging
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
# ---------------- FASTAPI ----------------
@app.get("/data")
async def get_data():
    return await run_scraper()


# Allow CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pyttsx3 TTS engine once
tts_engine = pyttsx3.init()



@app.post("/process_text/")
async def process_text(text: str):
    try:
        # Get response from RAG
        response_text = response(text)
        logging.info(f"RAG response: {response_text}")
        if not response_text:
            response_text = "Sorry, I could not generate a response."
        # Generate TTS audio file in a thread to avoid blocking
        filename = f"tts_{uuid.uuid4()}.mp3"
        loop = asyncio.get_event_loop()
        def tts_task():
            tts_engine.save_to_file(response_text, filename)
            tts_engine.runAndWait()
        await loop.run_in_executor(ThreadPoolExecutor(), tts_task)
        return {"response_text": response_text, "audio_file": filename}
    except Exception as e:
        logging.error(f"Error in /process_text/: {e}")
        return {"response_text": "Error: Could not process request.", "audio_file": None}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    return {"error": "File not found"}