import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import io
import requests
import json
import time

st.title("🤖 Voice Assistant Chatbot")

# Initialize session state and migrate old format if needed
if 'messages' not in st.session_state:
    st.session_state.messages = []
else:
    # Migrate old tuple format to new dictionary format
    migrated_messages = []
    for message in st.session_state.messages:
        if isinstance(message, tuple):
            # Old format: ("You", text) or ("Assistant", text)
            speaker, content = message
            role = "user" if speaker == "You" else "assistant"
            migrated_messages.append({"role": role, "content": content})
        elif isinstance(message, dict):
            # Already in new format
            migrated_messages.append(message)
    st.session_state.messages = migrated_messages

# Initialize session-related state
if 'session_id' not in st.session_state:
    st.session_state.session_id = ""  # Start with empty string like in curl
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'processing_audio' not in st.session_state:
    st.session_state.processing_audio = False
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None
if 'transcription_complete' not in st.session_state:
    st.session_state.transcription_complete = False

# Function to create new session
def create_new_session():
    try:
        api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8001")
        response = requests.post(f"{api_url}/create_session/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_id")
        else:
            st.error(f"Failed to create session: Status {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error creating session: {e}")
        return None

# Sidebar for settings and controls
with st.sidebar:
    st.header("Controls")
    
    # Session management
    if st.session_state.session_id:
        st.success(f"Session ID: {st.session_state.session_id[:8]}...")
        if st.button("🔄 New Session"):
            new_session_id = create_new_session()
            if new_session_id:
                st.session_state.session_id = new_session_id
                st.session_state.messages = []
                st.success("New session created!")
            st.rerun()
    else:
        if st.button("🆕 Create Session"):
            new_session_id = create_new_session()
            if new_session_id:
                st.session_state.session_id = new_session_id
                st.success("Session created!")
            st.rerun()
        st.info("Create a session or it will be auto-created with first message")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.header("Settings")
    enable_tts = st.checkbox("Enable Text-to-Speech", value=True)

# Display chat history
st.write("### Chat History:")
chat_container = st.container(height=400)  # Set fixed height for scrolling

with chat_container:
    if not st.session_state.messages:
        st.write("*No messages yet. Start a conversation!*")
    else:
        for i, message in enumerate(st.session_state.messages):
            # Handle both old and new formats safely
            if isinstance(message, dict):
                if message["role"] == "user":
                    st.write(f"**You:** {message['content']}")
                else:
                    st.write(f"**Assistant:** {message['content']}")
                    # Play audio for assistant messages if available
                    if enable_tts and "audio" in message:
                        st.audio(message["audio"], format="audio/mp3")
            else:
                # Fallback for any remaining tuple format
                speaker, content = message
                st.write(f"**{speaker}:** {content}")
            
            # Add separator between messages except for the last one
            if i < len(st.session_state.messages) - 1:
                st.write("---")

# Input section
st.write("### 💬 Send a Message:")

# Voice input section
st.write("#### 🎤 Voice Input:")
audio_input = st.audio_input("Record your voice message")

# Process voice input with buffer time
if audio_input:
    # Create a hash of the audio to detect new recordings
    audio_hash = hash(audio_input.getvalue())
    
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        st.session_state.processing_audio = True
        st.session_state.transcription_complete = False
        
        # Show processing indicator
        processing_placeholder = st.empty()
        processing_placeholder.info("🎵 Processing audio... Please wait.")
        
        try:
            recognizer = sr.Recognizer()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_input.getvalue())
                tmp.flush()
                tmp_path = tmp.name
            
            try:
                processing_placeholder.info("🔄 Transcribing speech...")
                with sr.AudioFile(tmp_path) as source:
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    
                    # Clear processing indicator and show success
                    processing_placeholder.success(f"✅ Transcribed: **{text}**")
                    st.session_state.transcribed_text = text
                    st.session_state.processing_audio = False
                    st.session_state.transcription_complete = True
                    
                    # Keep the success message visible and rerun to show text area
                    st.rerun()
                    
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except sr.UnknownValueError:
            processing_placeholder.error("❌ Could not understand the audio. Please try speaking more clearly.")
            st.session_state.processing_audio = False
            st.session_state.transcription_complete = False
        except sr.RequestError as e:
            processing_placeholder.error(f"❌ Speech recognition service error: {e}")
            st.session_state.processing_audio = False
            st.session_state.transcription_complete = False
        except Exception as e:
            processing_placeholder.error(f"❌ Speech recognition error: {e}")
            st.session_state.processing_audio = False
            st.session_state.transcription_complete = False

# Show text input area only if we have text or after transcription
if st.session_state.transcribed_text or not audio_input:
    st.write("#### ✏️ Text Input:")
    
    # Show different labels based on source
    if st.session_state.transcribed_text and st.session_state.transcription_complete:
        label = "Review and edit transcribed text:"
        help_text = "The text above was transcribed from your voice. You can edit it before sending."
    else:
        label = "Type your message:"
        help_text = "Type your message here or use the voice recorder above."
    
    text_input = st.text_area(
        label,
        value=st.session_state.transcribed_text,
        placeholder="Type your message here or use voice input above...",
        height=100,
        help=help_text,
        key="message_input"
    )
    
    # Buttons section - only show after transcription or if there's text
    if text_input.strip():  # Only show buttons if there's actual content
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            send_button = st.button("📤 Send Message", type="primary", use_container_width=True)
        
        with col2:
            if st.button("🧹 Clear Text", use_container_width=True):
                st.session_state.transcribed_text = ""
                st.session_state.transcription_complete = False
                st.rerun()
        
        with col3:
            if st.button("🔄 Re-record", use_container_width=True):
                st.session_state.transcribed_text = ""
                st.session_state.transcription_complete = False
                st.session_state.last_audio_hash = None  # Allow re-recording
                st.info("👆 Please use the voice recorder above to record again.")
                st.rerun()

# Show helpful message when processing
if st.session_state.processing_audio:
    st.info("⏳ Audio is being processed. Please wait for transcription to complete.")

# Process message sending
if 'send_button' in locals() and send_button and text_input and not st.session_state.processing_audio:
    # Add user message to history
    user_message = {
        "role": "user",
        "content": text_input
    }
    st.session_state.messages.append(user_message)
    
    # Show loading indicator
    with st.spinner("🤖 Assistant is thinking..."):
        # Get response from backend
        try:
            api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8001")
            
            # Prepare request data exactly like your curl command
            request_data = {
                "text": text_input,
                "session_id": st.session_state.session_id  # This will be "" for new sessions
            }
            
            # Send request to the process_text endpoint (correct path)
            response = requests.post(
                f"{api_url}/process_text/",  # Fixed: removed the duplicate path
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                },
                data=json.dumps(request_data),
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                # Get session ID from headers if provided
                session_id_header = response.headers.get("X-Session-ID")
                if session_id_header and session_id_header != st.session_state.session_id:
                    st.session_state.session_id = session_id_header
                    st.sidebar.success(f"Session created: {session_id_header[:8]}...")
                
                # Create placeholder for streaming response
                response_container = st.container()
                response_placeholder = st.empty()
                assistant_reply = ""
                
                # Stream the response
                with response_container:
                    st.write("**🤖 Assistant is responding:**")
                    try:
                        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                            if chunk:
                                assistant_reply += chunk
                                response_placeholder.markdown(f"{assistant_reply}")
                                time.sleep(0.01)  # Small delay for smoother streaming effect
                    except Exception as e:
                        st.error(f"❌ Streaming Error: {e}")
                        assistant_reply = "Sorry, there was an error receiving the response."
                
                # Generate TTS for the response
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_reply
                }
                
                if enable_tts and assistant_reply:
                    try:
                        with st.spinner("🔊 Generating speech..."):
                            tts = gTTS(text=assistant_reply, lang='en')
                            audio_buffer = io.BytesIO()
                            tts.write_to_fp(audio_buffer)
                            audio_buffer.seek(0)
                            assistant_message["audio"] = audio_buffer.getvalue()
                    except Exception as e:
                        st.error(f"❌ TTS Error: {e}")
                
                # Add assistant message to history
                st.session_state.messages.append(assistant_message)
                
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                except:
                    error_detail = f"Status {response.status_code}"
                
                error_message = {
                    "role": "assistant",
                    "content": f"Error: {error_detail}"
                }
                st.session_state.messages.append(error_message)
                st.error(f"❌ Backend Error: {error_detail}")
        
        except requests.exceptions.Timeout:
            error_message = {
                "role": "assistant",
                "content": "Error: Request timed out. Please try again."
            }
            st.session_state.messages.append(error_message)
            st.error("❌ Request timed out. Please try again.")
        except Exception as e:
            error_message = {
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }
            st.session_state.messages.append(error_message)
            st.error(f"❌ Request Error: {e}")
    
    # Clear the input fields after sending
    st.session_state.transcribed_text = ""
    st.session_state.transcription_complete = False
    st.rerun()

# Display conversation stats and tips in sidebar
with st.sidebar:
    st.write("---")
    st.write(f"**Messages:** {len(st.session_state.messages)}")
    if st.session_state.messages:
        user_msgs = len([m for m in st.session_state.messages if isinstance(m, dict) and m.get("role") == "user"])
        assistant_msgs = len([m for m in st.session_state.messages if isinstance(m, dict) and m.get("role") == "assistant"])
        st.write(f"**🧑 You:** {user_msgs} messages")
        st.write(f"**🤖 Assistant:** {assistant_msgs} messages")
    
    st.write("---")
    st.write("### 💡 Tips:")
    st.write("• Create session manually or auto-created with first message")
    st.write("• Record audio first, then review transcription")
    st.write("• Edit transcribed text before sending")
    st.write("• Use 'Re-record' to record again")
    st.write("• Toggle TTS on/off in settings")
    st.write("• Start new session to reset conversation")

# Footer
st.write("---")
st.write("*Voice Assistant Chatbot with Session Management - Record → Review → Edit → Send!*")