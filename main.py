from fastapi import FastAPI
from data import run_scraper
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
from openai import RealtimeClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pyttsx3
import uuid
import os

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
    response_text = f"You said: {text}"

    # Generate TTS audio file
    filename = f"tts_{uuid.uuid4()}.mp3"
    tts_engine.save_to_file(response_text, filename)
    tts_engine.runAndWait()

    return {"response_text": response_text, "audio_file": filename}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    return {"error": "File not found"}








# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# client = RealtimeClient(api_key=OPENAI_API_KEY)

# @app.post("/realtime-qa/")
# async def realtime_qa(request: Request):
#     data = await request.json()
#     question = data.get("question", "")

#     async def event_generator():
#         # Open a streaming chat completion with Realtime API
#         async for chunk in client.chat.stream(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant for Stevens Creek Chevrolet dealership."},
#                 {"role": "user", "content": question}
#             ],
#         ):
#             content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
#             if content:
#                 # Format as server-sent events (SSE) for streaming
#                 yield f"data: {content}\n\n"
#             await asyncio.sleep(0)  # Yield control to event loop

#     return StreamingResponse(event_generator(), media_type="text/event-stream")

# import json
# import os
# import asyncio
# import websockets
# from config import OPENAI_API_KEY
# from fastapi import FastAPI, WebSocket
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import StreamingResponse

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# WS_URL = "wss://api.openai.com/v1/realtime"

# @app.websocket("/ws/realtime")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()

#     async with websockets.connect(
#         WS_URL,
#         extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
#     ) as openai_ws:
#         # Receive questions from frontend WebSocket client
#         while True:
#             data = await websocket.receive_text()
#             question_data = json.loads(data)
#             question = question_data.get("question", "")

#             # Send start message to OpenAI realtime WebSocket
#             init_message = {
#                 "type": "start",
#                 "model": "gpt-4o",
#                 "messages": [
#                     {"role": "system", "content": "You are a helpful assistant."},
#                     {"role": "user", "content": question}
#                 ]
#             }
#             await openai_ws.send(json.dumps(init_message))

#             # Stream responses from OpenAI realtime WS, send back to frontend
#             async for message in openai_ws:
#                 response = json.loads(message)
#                 await websocket.send_text(message)  # Send raw OpenAI message to frontend
#                 if response.get("type") == "done":
#                     break
