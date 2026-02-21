import os
import json
import asyncio
import websockets
import base64
import wave
import time
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Your imports...
from rag import rag_response
from database.chat_history import create_new_session, save_chat_history
from utils.logging import Logger

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()
logger = Logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

async def save_audio_file(audio_chunks: list, session_id: str):
    """Save audio chunks as a WAV file"""
    try:
        combined_audio = b''.join(audio_chunks)
        output_dir = "audio_responses"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{output_dir}/response_{session_id}_{int(time.time())}.wav"
        with wave.open(output_filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes for PCM16
            wav_file.setframerate(24000)  # 24kHz sample rate
            wav_file.writeframes(combined_audio)
        logger.info(f"💾 Saved audio response: {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"Error saving audio file: {e}")
        return None

@app.websocket("/realtime")
async def realtime_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to /realtime websocket.")
    session_id = await create_new_session()
    logger.info(f"Created new session for realtime connection: {session_id}")

    user_transcript = ""
    ai_response = ""
    audio_chunks = []

    base_instructions =  "You are an intelligent voice assistant for Stevens Creek Chevrolet. "
    "Your role is to help customers with inquiries, provide real-time dealership information, "
    "and facilitate appointment booking. You should demonstrate empathetic customer service "
    "while intelligently promoting relevant products and services."

    try:
        async with websockets.connect(
        OPENAI_REALTIME_URL,
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        },
        ping_interval=None,
        ping_timeout=60
    ) as openai_ws:
            logger.info("Connected to OpenAI Realtime API")

            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": base_instructions, # Use base instructions initially
                    "voice": "alloy",
                    "speed": 1.0,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "gpt-4o-transcribe"},
                    "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000 
                }
                }
            }

            await openai_ws.send(json.dumps(session_config))
            logger.info("Sent initial session configuration")

            async def handle_client_audio():
                """Handle audio from client"""
                try:
                    while True:
                        message = await websocket.receive_bytes()
                        audio_base64 = base64.b64encode(message).decode('utf-8')
                        audio_event = {
                            "type": "input_audio_buffer.append",
                            "audio": audio_base64
                        }
                        await openai_ws.send(json.dumps(audio_event))
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Error handling client audio: {e}")

            async def handle_openai_responses():
                """Handle responses from OpenAI"""
                nonlocal user_transcript, ai_response, audio_chunks
                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        print("data:", data)
                        if data["type"] == "conversation.item.input_audio_transcription.completed":
                            user_transcript = data.get("transcript", "")
                            logger.info(f"👤 User transcript: {user_transcript}")
                            if user_transcript:
                                try:
                                    # Send transcript to client for display
                                    transcript_msg = {
                                        "type": "transcript",
                                        "content": user_transcript,
                                        "speaker": "user"
                                    }
                                    await websocket.send_text(json.dumps(transcript_msg))

                                    # 🧠 STEP 1: Get the RAG context and create a new, detailed prompt
                                    rag_enhanced_prompt = await rag_response(user_transcript, session_id)
                                    logger.info("🧠 Generated RAG context")
                                    
                                    # ⚙️ STEP 2: Update the session instructions with the new context
                                    session_update_with_rag = {
                                        "type": "session.update",
                                        "session": {
                                            "instructions": rag_enhanced_prompt
                                        }
                                    }
                                    await openai_ws.send(json.dumps(session_update_with_rag))
                                    logger.info("⚙️ Sent session update with RAG context")

                                    # ✅ STEP 3: Now, trigger the response generation
                                    response_create = {"type": "response.create"}
                                    await openai_ws.send(json.dumps(response_create))
                                    logger.info("✅ Triggered response creation")

                                except Exception as e:
                                    logger.error(f"Error processing RAG: {e}")
                        
                        # --- All other event handlers remain the same ---
                        elif data["type"] == "response.audio.delta":
                            try:
                                audio_bytes = base64.b64decode(data["delta"])
                                audio_chunks.append(audio_bytes)
                                audio_response = {
                                    "type": "audio",
                                    "audio": data["delta"],
                                }
                                await websocket.send_text(json.dumps(audio_response))
                            except Exception as e:
                                logger.error(f"Error sending audio to client: {e}")

                        elif data["type"] == "input_audio_buffer.speech_started":
                            logger.info("🎙️ Speech detected")
                            await websocket.send_text(json.dumps({"type": "speech_started"}))

                        elif data["type"] == "input_audio_buffer.speech_stopped":
                            logger.info("🔇 Speech stopped - processing...")
                            await websocket.send_text(json.dumps({"type": "speech_stopped"}))

                        elif data["type"] == "response.output_item.added":
                            logger.info("🤖 AI started responding")
                            await websocket.send_text(json.dumps({"type": "ai_speaking", "speaking": True}))

                        elif data["type"] == "response.done":
                            logger.info("✅ Response completed")
                            await websocket.send_text(json.dumps({"type": "ai_speaking", "speaking": False}))

                            if audio_chunks:
                                await save_audio_file(audio_chunks, session_id)
                                audio_chunks = []

                            if user_transcript and ai_response:
                                await save_chat_history(session_id, user_transcript, ai_response)
                                logger.info("💾 Saved conversation to history")
                                user_transcript = ""
                                ai_response = ""
                            
                            # Reset instructions for the next turn
                            reset_instructions = {
                                "type": "session.update",
                                "session": { "instructions": base_instructions }
                            }
                            await openai_ws.send(json.dumps(reset_instructions))
                            logger.info("🔄 Reset session instructions for next turn")


                        elif data["type"] == "error":
                            logger.error(f"❌ OpenAI API error: {data}")
                            error_msg = {"type": "error", "message": str(data.get("error", {}).get("message", "Unknown error"))}
                            await websocket.send_text(json.dumps(error_msg))

                        elif data["type"] == "response.text.delta":
                            ai_response += data.get("delta", "")

                        elif data["type"] in ["session.created", "session.updated", "input_audio_buffer.committed", "input_audio_buffer.cleared"]:
                            logger.info(f"✅ Acknowledged event: {data['type']}")

                except Exception as e:
                    logger.error(f"Error handling OpenAI responses: {e}")

            await asyncio.gather(
                handle_client_audio(),
                handle_openai_responses()
            )

    except Exception as e:
        logger.error(f"Error in realtime endpoint: {e}")
    finally:
        logger.info("WebSocket connection terminated.")