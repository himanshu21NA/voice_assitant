# Voice Assistant

This repository contains the source code for a sophisticated conversational AI system. The application provides a web-based user interface for users to interact with a chatbot using either text or voice. The backend is powered by a Retrieval-Augmented Generation (RAG) pipeline, enabling it to answer queries based on a corpus of dealership-specific data.

---

## Architecture Overview

The system follows a distributed, multi-tier architecture composed of three main services deployed on Render:

1.  **Frontend Service (Web Service)**: A Streamlit web application that serves as the user interface.
2.  **Backend Service (Web Service)**: A FastAPI application that exposes a REST API for the RAG pipeline, handles chat sessions, and streams responses.
3.  **ETL Service (Cron Job)**: A Python script responsible for periodically scraping dealership data and loading it into the database.

These services communicate with a central **PostgreSQL Database** that acts as the single source of truth for dealership data and chat history.

```
+----------------------+      +-----------------------+      +--------------------+
|      User Browser    |----->|   Frontend (Streamlit)|----->|  Backend (FastAPI) |
| (Voice/Text Input)   |      |      (Web Service)    |      |   (Web Service)    |
+----------------------+      +-----------------------+      +----------+---------+
                                        ^                           |
                                        | (API Calls)               | (RAG Pipeline)
                                        v                           v
+----------------------+      +-----------------------+      +----------+---------+
| External Services    |<-----|   ETL (Cron Job)      |<---->|  PostgreSQL DB     |
| (Dealership Website) |      | (Scraping & Loading)  |      | (Scraping & Chat)  |
+----------------------+      +-----------------------+      +--------------------+
```

---

## Tech Stack

-   **Frameworks**: `FastAPI`, `Streamlit`.
-   **AI & Embeddings**: `openai`, `langchain`, `faiss-cpu`, `sentence-transformers`.
-   **Database**: `psycopg2-binary`, `SQLAlchemy`.
-   **Web Scraping**: `playwright`, `beautifulsoup4`.
-   **Deployment**: `Docker`, `Render`.
-   **Other Key Libraries**: `python-dotenv`, `gtts`, `speechrecognition`.

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
│   ├── main.py           # FastAPI entry point
│   ├── rag.py            # RAG pipeline orchestrator
│   ├── config.py
│   ├── prompts.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app.py            # Streamlit entry point
│   ├── requirements.txt
│   └── Dockerfile
│
├── etl/
│   ├── data.py           # ETL entry point and scraping logic
│   ├── config.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── .gitignore
├── README.md             # This file
└── TDD.md                # Detailed Technical Design Document
```

---

## Deployment (Render)

The entire application is deployed on Render under a single project.

-   **Services**: The `frontend` and `backend` are deployed as **Web Services**. The `etl` service is deployed as a **Cron Job** that runs on a schedule.
-   **CI/CD**: Continuous deployment is enabled. Any push to the `main` branch will automatically trigger a new build and deployment for the relevant service(s) on Render.
-   **Environment**: All secrets (e.g., `DATABASE_URL`, `OPENAI_API_KEY`) are managed as a single secret group in Render and applied to all services.

---

## Local Development

The recommended way to run the project locally is with Docker.

### 1. Prerequisites
-   Docker and Docker Compose
-   Git

### 2. Clone the Repository
```sh
git clone https://github.com/himanshu21NA/voice_assitant.git
cd voice_assitant
```

### 3. Configure Environment
Create a `.env` file in the `backend` directory. This file will be used by the backend service.
```
# backend/.env
DATABASE_URL="your_postgresql_connection_string"
OPENAI_API_KEY="your_openai_api_key"
```

### 4. Run Services with Docker
You can build and run the services using their respective Dockerfiles.

**Run Backend:**
```sh
cd backend/
docker build -t voice-assistant-backend .
docker run --env-file .env -p 8001:8001 voice-assistant-backend
```

**Run Frontend:**
```sh
cd frontend/
# Ensure BACKEND_API_URL is set in your shell environment for the frontend to connect to the backend
export BACKEND_API_URL=http://localhost:8001
pip install -r requirements.txt
streamlit run app.py
```
> **Note**: The frontend is run locally with Streamlit's CLI for a better hot-reload development experience. It can also be run via Docker if preferred.

### 5. Access Services
-   **Frontend UI**: `http://localhost:8501`
-   **Backend API Docs**: `http://localhost:8001/docs`

## Deployment
- **Docker:** Use the provided Dockerfiles in `backend/` and `frontend/` to build and run containers locally or on any Docker-compatible platform.
- **Render (Docker):** Render deployment uses the Dockerfiles in each service folder. Push your code to GitHub, connect your repo to Render, and select "Docker" as the environment type for each service. Set environment variables in the Render dashboard as needed.

## Usage
- Access the Streamlit frontend at `http://localhost:8501` (or your Render URL).
- The backend API runs at `http://localhost:10000` (or your Render URL).
- Use the `/data` endpoint to trigger scraping and view dealership data.

## Contributing
Pull requests and issues are welcome! Please open an issue for bugs, feature requests, or questions.

## License
This project is licensed under the MIT License.

## Author
- Himanshu Verma ([himanshu21NA](https://github.com/himanshu21NA))
