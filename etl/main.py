from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging


# Local imports
from data import run_scraper

# ---------------- APP INIT ----------------
app = FastAPI()

# Allow only your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# ---------------- API ENDPOINTS ----------------
@app.post("/cron/run-scraper")
async def cron_run_scraper():
    """Dedicated endpoint for Render cron jobs."""
    logging.info("Cron job triggered: running scraper")
    return await run_scraper()