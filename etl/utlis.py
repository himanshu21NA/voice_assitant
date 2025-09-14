import re
import os
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
import asyncio
import httpx
from config import EXCLUDE_TERMS , BASE_URL, HEADERS
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