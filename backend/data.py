import asyncio
import json
import re
import requests
from playwright.async_api import async_playwright



# ---------------- CONFIG ----------------
PAGE_KEYWORDS = {
    "sales_specials": ["offer", "special", "lease", "rebate", "save"],
    "service_specials": ["service", "maintenance", "coupon", "brake", "oil change"],
    "ev_incentives": ["electric", "ev", "incentive", "rebate", "battery"],
    "financing_deals": ["financing", "apr", "loan", "payment", "credit", "rate"]
}

EXCLUDE_TERMS = ["home", "privacy", "contact", "terms", "cookie", "menu", "navigation", "footer"]

# ---------------- CONFIG ----------------
URLS = {
    "sales_specials": [
        "https://www.stevenscreekchevy.com/newspecials.html"
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
        "https://www.stevenscreekchevy.com/finance.aspx"
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
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
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

async def scrape_filtered_divs(url, keywords):
    import logging
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        max_retries = 2
        for attempt in range(max_retries):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=300000)
                await asyncio.sleep(5)
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt+1} failed to load {url}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Giving up on {url} after {max_retries} attempts.")
                    await browser.close()
                    return []
                await asyncio.sleep(2)

        divs = await page.locator("div").all_text_contents()
        filtered = await filter_texts(divs, keywords, EXCLUDE_TERMS)
        await browser.close()
        return filtered

def scrape_inventory():
    all_vehicles, page = [], 1
    while True:
        params = {"pn": page, "host": "www.stevenscreekchevy.com"}
        resp = requests.get(BASE_URL, headers=HEADERS, params=params)

        try:
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
                "fuel":v.get("VehicleFuelType"),
                "description": v.get("VehicleCommentsEncoded"),
                "url": v.get("VehicleDetailUrl"),
                "img": v.get("VehicleImageModel", {}).get("VehiclePhotoSrc"),
            }
            all_vehicles.append(vehicle)

        if page == 1:
            total_pages = data['Paging']['PaginationDataModel']['TotalPages']
        elif page >= total_pages:
            break
        page += 1
    return all_vehicles

# ---------------- MAIN FUNCTION ----------------
async def run_scraper():
    dataset = {}

    # Scrape specials
    for category, urls in URLS.items():
        keywords = PAGE_KEYWORDS.get(category, [])
        all_entries = []

        for url in urls:
            print(f"Scraping {category} from {url}")
            entries = await scrape_filtered_divs(url, keywords)
            print(f"  → Found {len(entries)} entries")
            all_entries.extend(entries)

        dataset[category] = all_entries
        print(f"  → Total {len(dataset[category])} entries in {category}")

    # Add vehicle inventory via API
    print("Fetching vehicle inventory via API...")
    dataset["vehicle_inventory"] = scrape_inventory()
    print(f"  → Found {len(dataset['vehicle_inventory'])} vehicles")

    # Save JSON
    with open("stevenscreek_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("\n✅ Data saved to stevenscreek_dataset.json")
    return dataset


def main():
    asyncio.run(run_scraper())


# ---------------- ENTRYPOINT ----------------
if __name__ == "__main__":
    main()
