
# Stevens Creek Chevrolet Voice Assistant

An intelligent voice assistant web application for Stevens Creek Chevrolet. This project helps customers with inquiries, provides real-time dealership information, and facilitates appointment booking. The assistant demonstrates empathetic customer service while intelligently promoting relevant products and services.

## Features
- **Voice and Text Chat:** Interact with the assistant using voice or text.
- **Real-Time Dealership Info:** Get up-to-date sales specials, service specials, EV incentives, and financing deals.
- **Appointment Booking:** Schedule service appointments directly through the assistant.
- **Vehicle Inventory Search:** Browse and inquire about available vehicles.
- **Empathetic Customer Service:** The assistant is designed to be helpful, friendly, and proactive.

## Tech Stack
- **Frontend:** Streamlit (Python)
- **Backend:** FastAPI (Python)
- **RAG (Retrieval-Augmented Generation):** OpenAI API, FAISS, Playwright
- **ETL:** Pandas, SQLAlchemy, psycopg2-binary
- **Database:** PostgreSQL (for scraped data)
- **Deployment:** Docker, Render

## Folder Structure

```
voice_assistant/
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── rag.py                # RAG pipeline and search logic
│   │   ├── data.py               # Data scraping/loading utilities
│   │   ├── config.py             # Configuration (API keys, settings)
│   │   ├── prompt.py             # Generation prompt(s)
│   │   └── utils.py              # Helper functions
│   ├── models/                   # (Optional) Database models
│   ├── requirements.txt          # Backend dependencies
│   ├── Dockerfile                # Backend Dockerfile
│   └── README.md                 # Backend-specific documentation
│
├── frontend/
│   ├── app.py                    # Streamlit entry point
│   ├── requirements.txt          # Frontend dependencies
│   ├── Dockerfile                # Frontend Dockerfile
│   └── README.md                 # Frontend-specific documentation
│
├── etl/
│   ├── etl.py                    # ETL scripts
│   ├── requirements.txt          # ETL dependencies
│   └── README.md                 # ETL-specific documentation
│
├── data/
│   ├── stevenscreek_dataset.json # Raw dataset
│   ├── cleaned_corpus.json       # Preprocessed corpus
│   └── ...                       # Other data files
│
├── .gitignore
├── README.md                     # Project overview
└── LICENSE
```

## Setup & Installation

### 1. Clone the repository
```sh
git clone https://github.com/himanshu21NA/voice_assitant.git
cd voice_assitant
```

### 2. Backend Setup
```sh
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Install Playwright browsers
playwright install
# Start FastAPI
uvicorn main:app --host 0.0.0.0 --port 10000
```

### 3. Frontend Setup
```sh
cd ../frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 4. ETL Setup
```sh
cd ../etl
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 5. Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required for backend).
- `DATABASE_URL`: PostgreSQL connection string (required for ETL and backend data saving).

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
