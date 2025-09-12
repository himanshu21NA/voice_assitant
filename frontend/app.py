import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import random
import io

st.title("🎤 Voice Assitant")

# Initialize session state
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []


# RAG import
import requests

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
    try:
        # Call FastAPI backend for RAG response
        api_url = "http://localhost:8000/process_text/"
        st.write(f"Sending request to: {api_url} with text: {text_input}")
        response = requests.post(api_url, params={"text": text_input})
        st.write(f"Response status code: {response.status_code}")
        st.write(f"Response content: {response.content}")
        if response.status_code == 200:
            try:
                data = response.json()
                st.write(f"Parsed JSON: {data}")
                assistant_reply = data.get("response_text", "Sorry, no response.")
            except Exception as e:
                assistant_reply = f"Error parsing JSON: {e}"
                st.write(assistant_reply)
            st.session_state.messages.append(("Assistant", assistant_reply))
            # Generate TTS for the response
            try:
                tts = gTTS(text=assistant_reply, lang='en')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                st.session_state.latest_audio = audio_buffer.getvalue()
            except Exception as e:
                st.error(f"TTS Error: {e}")
        else:
            error_msg = f"Error: Could not get response from backend. Status code: {response.status_code}"
            st.session_state.messages.append(("Assistant", error_msg))
            st.write(error_msg)
    except Exception as e:
        error_msg = f"Error: {e}"
        st.session_state.messages.append(("Assistant", error_msg))
        st.write(error_msg)
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