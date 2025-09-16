# Technical Design and Documentation: Real-time Voice Assistant

## 1. Overview

### 1.1. High-Level Description
This document outlines the technical design of the Real-time Voice Assistant, a sophisticated conversational AI system built with a WebSocket-first architecture. The application consists of a pure client-side HTML/JavaScript frontend that provides a real-time voice interface. The backend leverages the OpenAI Realtime API for low-latency transcription and text-to-speech (TTS), combined with a custom Retrieval-Augmented Generation (RAG) pipeline to provide contextually relevant, data-driven responses. A separate ETL pipeline periodically scrapes dealership data to keep the knowledge base current.

### 1.2. Goals and Scope
- **Goals**: To create a highly responsive, low-latency voice-native assistant that provides accurate answers based on a private knowledge base, running in any modern web browser with minimal client-side dependencies.
- **Scope**:
    - **Frontend**: A static HTML, CSS, and JavaScript single-page application that uses the Web Audio API and WebSockets to manage a persistent, real-time audio stream.
    - **Backend**: A high-performance FastAPI application that serves as a WebSocket proxy between the client and the OpenAI Realtime API, injecting RAG context into the conversation on the fly.
    - **ETL**: An automated cron job that scrapes dealership websites using Playwright and populates a PostgreSQL database.
    - **Database**: A PostgreSQL database to persist scraped data and conversation history.
    - **Deployment**: Containerized services (Docker) deployed to Render with CI/CD enabled.

---

## 2. Architecture Overview & Design Decisions

### 2.1. Description of Overall Architecture
The system uses a distributed, multi-tier architecture centered around real-time WebSocket communication.
1.  **Frontend**: A static HTML/JavaScript client served directly to the user's browser. It handles all user interface elements, captures microphone audio via the Web Audio API, and communicates exclusively through a WebSocket connection.
2.  **Backend Service**: A FastAPI application acting as an intelligent proxy. It manages a WebSocket connection with the client and a separate WebSocket connection with the OpenAI Realtime API. Its core responsibility is to intercept the user's transcribed text, use it to query the RAG pipeline, and dynamically update the AI's instructions with the retrieved context before a response is generated.
3.  **ETL Service**: A standalone Python script, run as a cron job, for data ingestion.
4.  **PostgreSQL Database**: The central data store for the RAG knowledge base and chat logs.

### 2.2. Major Design Choices and Rationale
- **Pure JavaScript Frontend**: The frontend was transitioned from Streamlit to a static HTML/JS page to gain maximum control over the real-time audio processing. This approach allows for direct use of the Web Audio API, enabling fine-tuned handling of audio capture, buffering, and a custom playback queue for smooth, uninterrupted TTS playback. It also results in an extremely lightweight and fast-loading client.
- **WebSocket-First Architecture**: The entire user interaction is handled over a single, persistent WebSocket connection. This is a deliberate choice to minimize latency, eliminate the overhead of repeated HTTP requests, and enable a truly real-time, back-and-forth conversation.
- **FastAPI (Backend)**: Chosen for its native support for asynchronous operations and WebSockets, making it ideal for handling concurrent, long-lived connections.
- **OpenAI Realtime API**: This specialized API is used for its ability to handle streaming audio input and provide low-latency transcription and TTS output, which is critical for a natural-feeling voice conversation.
- **On-the-Fly RAG Injection**: Instead of a simple request-response RAG model, the backend injects context *during* the live conversation. It waits for the transcription to complete, quickly fetches RAG context, and updates the OpenAI session's instructions before the AI generates its audio response. This makes the RAG process invisible to the end-user and keeps the conversation flowing.
- **Docker & Render**: Containerization with Docker ensures environment consistency. Render is used for its seamless Git-based deployment, CI/CD capabilities, and ability to host static sites, web services, and cron jobs within a single project.

### 2.3. Textual Architecture Diagram
```
+--------------+      (WebSocket)      +-----------------------+      (WebSocket)      +-----------------------+
| User Browser |<---------------------->| Backend (FastAPI)     |<---------------------->| OpenAI Realtime API   |
| (HTML/JS)    |                       | (RAG Injection Proxy) |                       | (Transcription & TTS) |
+--------------+                       +----------+------------+                       +-----------------------+
                                                  |
                                                  | (SQL Query)
                                                  v
                                           +----------+------------+
                                           |   PostgreSQL DB     |
                                           | (Scraped Data & Chat) |
                                           +---------------------+
                                                  ^
                                                  | (SQL Write)
                                           +------|--------------+
                                           | ETL (Cron Job)      |
                                           | (Playwright Scraper)|
                                           +---------------------+
```

---

## 3. Modules & Responsibilities

### 3.1. `frontend/`
-   **`realtime_rag_chat.html`**: A single, self-contained file that includes all HTML structure, CSS styling, and JavaScript logic.
    -   **UI Management**: Handles DOM manipulation for displaying status updates, conversation transcripts, and control states (e.g., enabling/disabling buttons).
    -   **Audio Capture**: Uses the Web Audio API (`AudioContext`, `ScriptProcessorNode`) to capture raw PCM audio from the user's microphone.
    -   **WebSocket Communication**: Establishes and manages the WebSocket connection to the backend, sends the captured audio, and processes incoming JSON messages from the server.
    -   **Audio Playback**: Implements a custom audio queue to handle incoming TTS audio chunks. It decodes the PCM data and schedules it for seamless playback using the Web Audio API, ensuring a continuous stream of audio even if chunks arrive with slight network jitter.

### 3.2. `backend/`
-   **`main.py`**: The FastAPI entry point. Defines the `/realtime` WebSocket endpoint. It manages the client connection and the connection to OpenAI, acting as the central orchestrator for the entire real-time conversation flow.
-   **`rag.py`**: Contains the `rag_response` function. This function is called by `main.py` after a user transcript is received. It performs the full RAG pipeline: loads data, builds a corpus, enhances the query, performs a vector search, and returns a formatted prompt string containing the fresh context.
-   **`database/data_loader.py`**: Fetches the latest scraped dataset from the PostgreSQL `scraped_data` table.
-   **`database/chat_history.py`**: Manages creating session IDs and saving the final user query and assistant response to the `chat_history` table.
-   **`embedding/`, `processing/`, `utils/`**: Contain the helper modules for the RAG pipeline (embedding, text processing, FAISS indexing) and shared utilities like the custom logger.

### 3.3. `etl/`
-   **`data.py`**: The entry point and core logic for the ETL process. It uses Playwright to scrape dealership websites, processes the data, and saves the final dataset to the PostgreSQL `scraped_data` table.

---

## 4. Data Flow

1.  **ETL Data Ingestion (Asynchronous)**:
    -   The Render cron job triggers the `etl/data.py` script on a schedule.
    -   Playwright launches a headless browser to scrape data from target websites.
    -   The scraped data is structured into a JSON object and inserted into the `scraped_data` table in the PostgreSQL database.

2.  **Real-time Conversation Flow**:
    1.  **Connection**: The user clicks "Start Recording" in the browser, which initiates a WebSocket connection from the client-side JavaScript to the backend's `/realtime` endpoint.
    2.  **Proxy Connection**: The backend, upon receiving the client connection, immediately establishes its own WebSocket connection to the OpenAI Realtime API.
    3.  **Audio Streaming**: The JavaScript in the frontend uses the Web Audio API to capture raw PCM audio chunks from the user's microphone and sends them continuously over the WebSocket to the backend.
    4.  **Audio Forwarding**: The backend forwards these audio chunks directly to the OpenAI API.
    5.  **Transcription**: OpenAI's API performs real-time transcription and sends a `conversation.item.input_audio_transcription.completed` event back to the backend when the user stops speaking.
    6.  **RAG Intervention**:
        -   The backend intercepts the completed transcript.
        -   It immediately calls the `rag_response` function with the transcript text.
        -   `rag.py` executes the entire RAG pipeline (data loading, embedding, search) and returns a new, context-rich prompt.
    7.  **Instruction Update**: The backend sends a `session.update` event to the OpenAI API, dynamically replacing the session's instructions with the new RAG-enhanced prompt.
    8.  **Response Trigger**: The backend then sends a `response.create` event to OpenAI, telling it to generate a response based on the *new* instructions.
    9.  **TTS Streaming**: OpenAI generates the response and streams the TTS audio back to the backend. The backend forwards the base64-encoded audio chunks to the client's JavaScript.
    10. **Client-Side Playback**: The JavaScript code decodes the audio chunks and adds them to a playback queue, which uses the Web Audio API to play them seamlessly.
    11. **Logging**: Once the response is complete, the backend saves the user's query and the final AI response to the `chat_history` table.
    12. **Cycle**: The session instructions are reset, and the system is ready for the next user utterance.

---

## 5. API Documentation

The backend exposes a single WebSocket endpoint for real-time communication.

-   **Endpoint**: `WS /realtime`
    -   **Description**: Manages a full-duplex communication channel for streaming audio and exchanging conversational events.
    -   **Connection Flow**:
        1.  Client connects to this endpoint.
        2.  Backend accepts the connection and establishes its own connection to the OpenAI Realtime API.
        3.  Backend sends an initial session configuration to OpenAI.
    -   **Client-to-Server Messages**:
        -   **Type**: `bytes`
        -   **Content**: Raw PCM audio data from the microphone.
    -   **Server-to-Client Messages (JSON)**:
        -   `{"type": "transcript", "content": "...", "speaker": "user"}`: A completed user transcript.
        -   `{"type": "audio", "audio": "<base64_encoded_pcm>"}`: A chunk of the AI's audio response.
        -   `{"type": "speech_started"}` / `{"type": "speech_stopped"}`: Indicates when the user starts/stops speaking.
        -   `{"type": "ai_speaking", "speaking": true/false}`: Indicates when the AI starts/stops generating a response.
        -   `{"type": "error", "message": "..."}`: Reports an error from the OpenAI API.

---

## 6. Database Schema

The system uses a PostgreSQL database with two primary tables.

### `scraped_data` Table
Stores the knowledge base for the RAG pipeline.

| Column      | Type                      | Constraints        | Description                               |
|-------------|---------------------------|--------------------|-------------------------------------------|
| `id`        | `SERIAL`                  | `PRIMARY KEY`      | Unique identifier for the scrape record.  |
| `category`  | `TEXT`                    | `NOT NULL`         | The category of the scrape (e.g., "stevenscreek"). |
| `content`   | `JSONB`                   | `NOT NULL`         | The entire scraped dataset, stored as a JSON object. |
| `created_at`| `TIMESTAMPTZ`             | `DEFAULT NOW()`    | Timestamp of when the record was inserted. |

### `chat_history` Table
Logs conversations for session management and analytics.

| Column               | Type                      | Constraints               | Description                                       |
|----------------------|---------------------------|---------------------------|---------------------------------------------------|
| `id`                 | `SERIAL`                  | `PRIMARY KEY`             | Unique identifier for the chat entry.             |
| `session_id`         | `UUID`                    | `NOT NULL`                | Unique identifier for a conversation session.     |
| `user_query`         | `TEXT`                    | `NOT NULL`                | The user's transcribed message.                   |
| `assistant_response` | `TEXT`                    | `NOT NULL`                | The assistant's final text response.              |
| `created_at`         | `TIMESTAMP`               | `DEFAULT NOW()`           | Timestamp of the interaction.                     |

---

## 7. Deployment Instructions

### 7.1. Production Deployment (Render)
The application is deployed on Render as a single project with three services.

-   **Frontend**: Deployed as a **Static Site**. Render serves the `realtime_rag_chat.html` file directly.
-   **Backend**: Deployed as a **Web Service**. Render builds and deploys it using its `Dockerfile`.
-   **ETL**: Deployed as a **Cron Job** that runs `python etl/data.py` on a defined schedule.
-   **CI/CD**: Continuous deployment is enabled via GitHub. A push to the main branch automatically triggers a new build and deployment for the corresponding service.
-   **Environment Variables**: Secrets (`DATABASE_URL`, `OPENAI_API_KEY`) are managed in a secret group within Render and applied to all relevant services.

### 7.2. Local Development
1.  **Clone Repository**: `git clone <repository_url>`
2.  **Configure Environment**: Create a `.env` file in the `backend` directory with `DATABASE_URL` and `OPENAI_API_KEY`.
3.  **Run Backend Service**:
    ```sh
    cd backend/
    docker build -t voice-assistant-backend .
    docker run --env-file .env -p 8001:8001 voice-assistant-backend
    ```
4.  **Run Frontend**:
    -   Navigate to the `frontend` directory.
    -   Open the `realtime_rag_chat.html` file directly in a modern web browser (like Chrome or Firefox).
5.  **Access Services**:
    -   The application will be running in your browser tab. Ensure the backend is running and accessible at `localhost:8001`.

---

## 8. Dependencies

-   **Frontend**: A modern web browser with support for WebSockets and the Web Audio API. No other dependencies.
-   **Backend**: `FastAPI`, `websockets`, `openai`, `langchain`, `faiss-cpu`, `sentence-transformers`, `psycopg2-binary`.
-   **ETL**: `playwright`, `psycopg2-binary`.

---

## 9. Developer Notes

The real-time, bidirectional voice functionality was developed as a proof-of-concept in a single day. This rapid development cycle means that while the core features are functional, some aspects may be unrefined or lack the robustness of a production-grade system. The primary goal was to quickly validate the architecture using OpenAI's Realtime API. As such, there may be unknown edge cases or areas for improvement that were not addressed during this initial build. This context is important when considering the limitations below.

---

## 10. Limitations & Assumptions

-   **Scraping Fragility**: The ETL process is tightly coupled to the HTML structure of the target websites and will break if they are redesigned.
-   **Network Dependency**: The real-time experience is highly sensitive to network latency between the client, the backend, and the OpenAI API.
-   **Browser Compatibility**: The frontend relies on modern browser APIs (Web Audio, WebSockets) and may not work on older browsers.
-   **Authentication**: The system lacks user authentication and authorization. All users are anonymous and share the same access.
-   **Cost**: The use of the OpenAI Realtime API can be more expensive than standard text-based models due to the continuous streaming and processing.
