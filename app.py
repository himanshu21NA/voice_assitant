import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import random
import io

st.title("🎤 Simple Voice Chat")

# Initialize session state
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Dummy responses
dummy_responses = [
    "That's interesting!",
    "I understand what you mean.",
    "Tell me more about that.",
    "That sounds great!",
    "I see your point.",
    "Thanks for sharing that with me.",
    "That's a good question.",
    "I think you're right about that."
]

# Voice input
audio_input = st.audio_input("Record something")
if audio_input:
    st.write("Audio received!")
    try:
        recognizer = sr.Recognizer()
        # Use BytesIO instead of temporary file
        audio_bytes = io.BytesIO(audio_input.getvalue())
        
        # Create a temporary file with proper cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_input.getvalue())
            tmp.flush()  # Ensure data is written
            tmp_path = tmp.name
        
        try:
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                st.success(f"Transcribed: {text}")
                st.session_state.transcribed_text = text
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except sr.UnknownValueError:
        st.error("Could not understand the audio")
    except sr.RequestError as e:
        st.error(f"Speech recognition service error: {e}")
    except Exception as e:
        st.error(f"Speech recognition error: {e}")

# Text input
text_input = st.text_input("Type something:", value=st.session_state.transcribed_text, key="text_input")

# Clear button
if st.button("Clear"):
    st.session_state.transcribed_text = ""
    st.rerun()  # Refresh to clear the input

# Send button
if st.button("Send") and text_input:
    # Add messages to history
    st.session_state.messages.append(("You", text_input))
    response = random.choice(dummy_responses)
    st.session_state.messages.append(("Assistant", response))
    
    # Generate TTS for the response
    try:
        tts = gTTS(text=response, lang='en')
        # Use BytesIO for in-memory audio handling
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Store audio in session state
        st.session_state.latest_audio = audio_buffer.getvalue()
        
    except Exception as e:
        st.error(f"TTS Error: {e}")
    
    # Clear the text input
    st.session_state.transcribed_text = ""
    st.rerun()

# Display conversation history
if st.session_state.messages:
    st.write("### Conversation:")
    for i, (speaker, message) in enumerate(st.session_state.messages):
        st.write(f"**{speaker}:** {message}")
        
        # Play audio for the latest assistant message
        if (speaker == "Assistant" and 
            i == len(st.session_state.messages) - 1 and 
            'latest_audio' in st.session_state):
            st.audio(st.session_state.latest_audio, format="audio/mp3")

# import streamlit as st
# import asyncio
# import websockets
# import json

# st.title("WebSocket Connection Test")

# async def test_connection():
#     uri = "ws://localhost:8000/ws/realtime"
#     try:
#         async with websockets.connect(uri, timeout=5) as websocket:
#             # Send a test message
#             test_message = {"test": "connection"}
#             await websocket.send(json.dumps(test_message))
            
#             # Try to receive a response
#             try:
#                 response = await asyncio.wait_for(websocket.recv(), timeout=5)
#                 return f"Success! Server responded: {response}"
#             except asyncio.TimeoutError:
#                 return "Connected but no response received within 5 seconds"
                
#     except ConnectionRefusedError:
#         return "Connection refused - server not running or wrong port"
#     except Exception as e:
#         return f"Connection failed: {e}"

# if st.button("Test WebSocket Connection"):
    with st.spinner("Testing connection..."):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_connection())
            st.write(result)
        finally:
            loop.close()