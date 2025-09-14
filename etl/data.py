import logging
import asyncio
import os
import time
import psycopg2
from psycopg2.extras import Json
from playwright.async_api import async_playwright
from config import PAGE_KEYWORDS,URLS
from utlis import scrape_filtered_divs, scrape_inventory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- POSTGRES SAVE ----------------

def save_to_postgres(dataset):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set in environment variables")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scraped_data (
        id SERIAL PRIMARY KEY,
        category TEXT NOT NULL,
        content JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    );
    """)

    cur.execute(
        """
        INSERT INTO scraped_data (category, content, created_at)
        VALUES (%s, %s, NOW())
        """,
        ("stevenscreek", Json(dataset)) 
    )

    conn.commit()
    cur.close()
    conn.close()
    logging.info("Dataset inserted into Postgres with timestamp")
# ---------------- MAIN SCRAPER ----------------
async def run_scraper():
    
    start_time = time.time()
    dataset = {}

    def remove_substring_duplicates(entries):
        # Sort by length, longest first
        sorted_entries = sorted(entries, key=len, reverse=True)
        unique_entries = []

        for i, entry in enumerate(sorted_entries):
            # Keep only if not a substring of any already accepted entry
            if not any(entry in kept for kept in unique_entries):
                unique_entries.append(entry)

        return unique_entries


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for category, urls in URLS.items():
            keywords = PAGE_KEYWORDS.get(category, [])
            tasks = [scrape_filtered_divs(url, keywords, browser) for url in urls]
            results = await asyncio.gather(*tasks)
            all_entries = [entry for sublist in results for entry in sublist]

            # Deduplicate substrings
            dataset[category] = remove_substring_duplicates(all_entries)

            logging.info(f" → Total {len(dataset[category])} entries in {category}")

        await browser.close()

    logging.info("Fetching vehicle inventory via API...")
    dataset["vehicle_inventory"] = await scrape_inventory()
    logging.info(f" → Found {len(dataset['vehicle_inventory'])} vehicles")

    save_to_postgres(dataset)
    
    # with open("local_dataset.json", "w") as f:
    #     json.dump(dataset, f, indent=2)
    # print("Dataset saved to local_dataset.json")
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"✅ Scraper completed in {total_time:.2f} seconds.")
    return dataset

if __name__ == "__main__":
    logging.info("Running scraper as standalone job...")
    asyncio.run(run_scraper())
    logging.info("Scraper finished.")
