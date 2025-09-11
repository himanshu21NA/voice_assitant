# import asyncio
# import json
# from playwright.async_api import async_playwright


# async def scrape_vehicle_inventory(page, base_url):
#     await page.goto(base_url, wait_until="domcontentloaded", timeout=120000)
#     await page.wait_for_selector("div.vehicle-card[data-vehicle-information]", timeout=120000)

#     # Step 1: Try to set "Show: 96" (fewer pages)
#     try:
#         await page.locator("button.pagination-dropdown").click()
#         await page.locator("button.custom-option[data-value='96']").click()
#         await page.wait_for_timeout(120000)
#         print("Changed page size to 96")
#     except:
#         print("Could not change page size, defaulting to 12 per page.")

#     all_vehicles = []
#     page_num = 1

#     # Step 2: Loop through pagination
#     while True:
#         print(f"Scraping page {page_num}...")

#         # Scrape all vehicles on this page
#         cards = await page.locator("div.vehicle-card[data-vehicle-information]").all()
#         for el in cards:
#             vehicle = {
#                 "vin": await el.get_attribute("data-vin"),
#                 "make": await el.get_attribute("data-make"),
#                 "model": await el.get_attribute("data-model"),
#                 "year": await el.get_attribute("data-year"),
#                 "trim": await el.get_attribute("data-trim"),
#                 "price": await el.get_attribute("data-dotagging-item-price"),
#                 "stocknum": await el.get_attribute("data-stocknum"),
#                 "msrp": await el.get_attribute("data-msrp"),
#                 "ext_color": await el.get_attribute("data-extcolor"),
#                 "int_color": await el.get_attribute("data-intcolor"),
#                 "mileage": await el.locator(".vehicle-mileage").text_content()
#                            if await el.locator(".vehicle-mileage").count() else None,
#                 "url": await el.locator("a.vehicle-title").get_attribute("href"),
#             }
#             all_vehicles.append(vehicle)

#         # Step 3: Click Next if available
#         next_btn = page.locator("li.pagination__item--next a.pagination__link").first
#         if await next_btn.count() == 0:
#             break  # no next page

#         # Capture current VINs to detect DOM change
#         prev_vins = await page.eval_on_selector_all(
#             "div.vehicle-card[data-vehicle-information]",
#             "els => els.map(e => e.getAttribute('data-vin'))"
#         )

#         await next_btn.click()

#         # Wait until new VINs appear
#         await page.wait_for_function(
#             """prev => {
#                 const vins = Array.from(document.querySelectorAll("div.vehicle-card[data-vehicle-information]"))
#                                    .map(e => e.getAttribute("data-vin"));
#                 return vins.some(v => !prev.includes(v));
#             }""",
#             arg=prev_vins,
#             timeout=15000
#         )

#         page_num += 1

#     return all_vehicles


# async def main():
#     url = "https://www.stevenscreekchevy.com/searchall.aspx"

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context()
#         page = await context.new_page()

#         inventory = await scrape_vehicle_inventory(page, url)

#         await browser.close()

#         with open("vehicle_inventory.json", "w", encoding="utf-8") as f:
#             json.dump(inventory, f, ensure_ascii=False, indent=2)

#         print(f"Scraped {len(inventory)} vehicles. Saved to vehicle_inventory.json")


# if __name__ == "__main__":
#     asyncio.run(main())

import requests
import json

BASE_URL = "https://www.stevenscreekchevy.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/16823/3165452"

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "referer": "https://www.stevenscreekchevy.com/searchall.aspx",
}

all_vehicles = []
page = 1

while True:
    params = {
        "pn": page,
        "host": "www.stevenscreekchevy.com",
        "displayCardsShown": "NaN",
    }
    resp = requests.get(BASE_URL, headers=headers, params=params)
    data = resp.json()
    print(data.get("DisplayCards")[0])
    print(len(data.get("DisplayCards")))
    # Check where the inventory lives — often under "results" or "vehicles"
    vehicles = data.get("vehicles") or data.get("results") or data.get("inventory", [])
    if not vehicles:
        break

    all_vehicles.extend(vehicles)
    print(f"Fetched page {page} with {len(vehicles)} vehicles")
    page += 1

print(f"Total scraped: {len(all_vehicles)} vehicles")

with open("api_vehicle_inventory.json", "w", encoding="utf-8") as f:
    json.dump(all_vehicles, f, ensure_ascii=False, indent=2)

