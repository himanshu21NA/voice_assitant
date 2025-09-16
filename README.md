# Real-time Voice Assistant

This repository contains the source code for a real-time, bidirectional voice assistant. The application uses a pure HTML/JavaScript frontend and a Python backend to create a low-latency conversational experience, powered by OpenAI's Realtime API and a custom Retrieval-Augmented Generation (RAG) pipeline.

---

### Developer Note
This project, particularly the real-time voice functionality, was built as a proof-of-concept in a single day. Due to this rapid development timeline, the project is currently set up for **local execution only** and has not been deployed to any cloud services like Render. The focus was on validating the architecture, so some areas may be unrefined.

---

## Architecture Overview

The system uses a WebSocket-first architecture to achieve low-latency communication.

1.  **Frontend**: A static HTML/JavaScript page that captures microphone audio using the Web Audio API and streams it to the backend via a WebSocket. It also handles playing back the AI's audio response.
2.  **Backend**: A FastAPI (Python) application that acts as an intelligent proxy. It manages the WebSocket connection from the client and a second WebSocket connection to the OpenAI Realtime API. It injects RAG context on-the-fly by intercepting the user's transcript and updating the AI's instructions before it responds.
3.  **ETL**: A manual script that scrapes dealership data using Playwright and stores it in a PostgreSQL database.
4.  **Database**: A local PostgreSQL instance to store the scraped data for the RAG pipeline and to log chat history.

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
                                           | ETL (Manual Script) |
                                           | (Playwright Scraper)|
                                           +---------------------+
```

---

## Tech Stack

-   **Frontend**: HTML, CSS, JavaScript (with Web Audio API)
-   **Backend**: `FastAPI`, `WebSockets`
-   **AI & Embeddings**: `openai`, `langchain`, `faiss-cpu`, `sentence-transformers`
-   **Database**: `psycopg2-binary` (PostgreSQL)
-   **Web Scraping**: `playwright`
-   **Containerization**: `Docker`

---

## Project Structure
```
voice_assistant/
│
├── backend/
│   ├── database/
│   ├── embedding/
│   ├── processing/
│   ├── utils/
│   ├── main.py           # FastAPI WebSocket proxy
│   ├── rag.py            # RAG pipeline
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   └── realtime_rag_chat.html  # The single-page frontend
│
├── etl/
│   └── data.py           # Manual ETL script
│
├── .gitignore
├── README.md             # This file
└── TDD.md                # Detailed Technical Design Document
```

---

## Local Setup and Execution

This project is designed to be run locally.

### 1. Prerequisites
-   Docker
-   A modern web browser (e.g., Chrome, Firefox)
-   Git
-   A running PostgreSQL instance

### 2. Clone the Repository
```sh
git clone https://github.com/himanshu21NA/voice_assitant.git
cd voice_assitant
```

### 3. Configure Environment
Create a `.env` file in the `backend` directory with your database connection string and OpenAI API key.
```
# backend/.env
DATABASE_URL="postgresql://user:password@host:port/dbname"
OPENAI_API_KEY="your_openai_api_key"
```

### 4. Run the ETL Process
You must populate the database with data for the RAG pipeline to work. Run the ETL script manually:
```sh
cd etl/
pip install -r requirements.txt
python data.py
```
> **Note**: This requires Playwright browsers to be installed. If you haven't installed them, run `playwright install`.

### 5. Run the Backend
The backend runs in a Docker container.
```sh
cd backend/
docker build -t voice-assistant-backend .
docker run --env-file .env -p 8001:8001 --network="host" voice-assistant-backend
```
> **Note**: `--network="host"` is used to easily connect to a PostgreSQL database running on `localhost`. Adjust if your database is hosted elsewhere.

### 6. Run the Frontend
Navigate to the `frontend` directory and open the `realtime_rag_chat.html` file directly in your web browser.
```sh
# On macOS
open frontend/realtime_rag_chat.html
# On Windows
start frontend/realtime_rag_chat.html
# On Linux
xdg-open frontend/realtime_rag_chat.html
```

The application should now be running in your browser tab. Click "Start Recording" to begin.
