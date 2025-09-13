import logging
import asyncio
import json
import re
import os
import httpx
import time
import psycopg2
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- CONFIG ----------------
PAGE_KEYWORDS = {
    "sales_specials": ["offer", "special", "lease", "rebate", "save"],
    "service_specials": ["service", "maintenance", "coupon", "brake", "oil change"],
    "ev_incentives": ["electric", "ev", "incentive", "rebate", "battery"],
    "financing_deals": ["financing", "apr", "loan", "payment", "credit", "rate"],
}

EXCLUDE_TERMS = ["home", "privacy", "contact", "terms", "cookie", "menu", "navigation", "footer"]

URLS = {
   "sales_specials": [
       "https://www.stevenscreekchevy.com/newspecials.html",
   ],
   "service_specials": [
       "https://www.stevenscreekchevy.com/service-parts-specials.html",
       "https://www.stevenscreekchevy.com/service",
       "https://www.stevenscreekchevy.com/serviceapptform",
       "https://www.stevenscreekchevy.com/service-department-san-jose-ca",
       "https://www.stevenscreekchevy.com/onstar.html",
       "https://www.stevenscreekchevy.com/brake-service-san-jose-ca",
       "https://www.stevenscreekchevy.com/tire-rotation-san-jose-ca",
       "https://www.stevenscreekchevy.com/new-tires",
       "https://www.stevenscreekchevy.com/mobile-service-plus",
   ],
   "ev_incentives": [
       "https://www.stevenscreekchevy.com/ev-incentives",
       "https://www.stevenscreekchevy.com/electric-vehicles",
   ],
   "financing_deals": [
       "https://www.stevenscreekchevy.com/finance.aspx",
   ],
}

# Vehicle API
BASE_URL = "https://www.stevenscreekchevy.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/16823/3165452"
HEADERS = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
    "referer": "https://www.stevenscreekchevy.com/searchall.aspx",
}

# ---------------- HELPERS ----------------
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip()


async def filter_texts(texts, keywords, exclude_terms):
    filtered, seen = [], set()
    for text in texts:
        cleaned = clean_text(text)
        lower_text = cleaned.lower()
        if any(kw in lower_text for kw in keywords) and not any(ex in lower_text for ex in exclude_terms):
            if cleaned not in seen and len(cleaned) > 20:
                seen.add(cleaned)
                filtered.append(cleaned)
    return filtered


async def scrape_filtered_divs(url, keywords, browser):
    logging.info(f"Scraping {url}")
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=180000)
        await asyncio.sleep(5)
        divs = await page.locator("div").all_text_contents()
        filtered = await filter_texts(divs, keywords, EXCLUDE_TERMS)
        logging.info(f" → {len(filtered)} entries from {url}")
        return filtered
    except Exception as e:
        logging.error(f"Failed {url}: {e}")
        return []
    finally:
        await page.close()


async def scrape_inventory():
    all_vehicles, page = [], 1
    async with httpx.AsyncClient() as client:
        while True:
            params = {"pn": page, "host": "www.stevenscreekchevy.com"}
            try:
                resp = await client.get(BASE_URL, headers=HEADERS, params=params, timeout=60)
                data = resp.json()
            except Exception:
                break

            cards = data.get("DisplayCards", [])
            if not cards:
                break

            for card in cards:
                v = card.get("VehicleCard", {})
                vehicle = {
                    "vin": v.get("VehicleVin") or (v.get("VehicleImageCarouselModel") or {}).get("Vin"),
                    "make": v.get("VehicleMake"),
                    "model": v.get("VehicleModel"),
                    "year": v.get("VehicleYear"),
                    "trim": v.get("VehicleTrim"),
                    "price": v.get("TaggingPrice"),
                    "stocknum": v.get("VehicleStockNumber"),
                    "msrp": v.get("VehicleMsrp"),
                    "ext_color": v.get("ExteriorColorLabel"),
                    "int_color": v.get("InteriorColorLabel"),
                    "mileage": v.get("Mileage"),
                    "condition": v.get("VehicleCondition"),
                    "fuel": v.get("VehicleFuelType"),
                    "description": v.get("VehicleCommentsEncoded"),
                    "url": v.get("VehicleDetailUrl"),
                    "img": v.get("VehicleImageModel", {}).get("VehiclePhotoSrc"),
                }
                all_vehicles.append(vehicle)

            if page == 1:
                total_pages = data["Paging"]["PaginationDataModel"]["TotalPages"]
            elif page >= total_pages:
                break
            page += 1
    return all_vehicles

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
        ("stevenscreek", json.dumps(dataset))
    )

    conn.commit()
    cur.close()
    conn.close()
    logging.info("✅ Dataset inserted into Postgres with timestamp")

# ---------------- MAIN SCRAPER ----------------
async def run_scraper():
    
    start_time = time.time()
    dataset = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for category, urls in URLS.items():
            keywords = PAGE_KEYWORDS.get(category, [])
            tasks = [scrape_filtered_divs(url, keywords, browser) for url in urls]
            results = await asyncio.gather(*tasks)
            all_entries = [entry for sublist in results for entry in sublist]
            dataset[category] = all_entries
            logging.info(f" → Total {len(all_entries)} entries in {category}")

        await browser.close()

    logging.info("Fetching vehicle inventory via API...")
    dataset["vehicle_inventory"] = await scrape_inventory()
    logging.info(f" → Found {len(dataset['vehicle_inventory'])} vehicles")

    save_to_postgres(dataset)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"✅ Scraper completed in {total_time:.2f} seconds.")
    return dataset

if __name__ == "__main__":
    logging.info("Running scraper as standalone job...")
    asyncio.run(run_scraper())
    logging.info("Scraper finished.")
