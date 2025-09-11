# 
import asyncio
import json
import re
from playwright.async_api import async_playwright

PAGE_KEYWORDS = {
    "sales_specials": ["offer", "special", "lease", "rebate", "save"],
    "service_specials": ["service", "maintenance", "coupon", "brake", "oil change"],
    "ev_incentives": ["electric", "ev", "incentive", "rebate", "battery"],
    "vehicle_inventory": ["inventory", "vehicle", "model", "trim", "chevrolet", "chevy"],
    "financing_deals": ["financing", "apr", "loan", "payment", "credit", "rate"]
}

EXCLUDE_TERMS = ["home", "privacy", "contact", "terms", "cookie", "menu", "navigation", "footer"]

def clean_text(text):
    # Remove excess whitespace, newlines, tabs
    text = re.sub(r'\s+', ' ', text)
    # Remove non-ASCII characters (optional)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove trailing and leading spaces
    text = text.strip()
    return text

async def filter_texts(texts, keywords, exclude_terms):
    filtered = []
    seen = set()
    for text in texts:
        cleaned = clean_text(text)
        lower_text = cleaned.lower()
        if any(kw in lower_text for kw in keywords) and not any(ex in lower_text for ex in exclude_terms):
            # Deduplicate similar entries based on cleaned text
            if cleaned not in seen and len(cleaned) > 20:  # minimum length filter
                seen.add(cleaned)
                filtered.append(cleaned)
    return filtered

async def scrape_filtered_divs(page, url, keywords):
    await page.goto(url, wait_until="load", timeout=120000)
    await asyncio.sleep(10)  # wait for dynamic content

    divs = await page.locator("body > div:not(header) :not(footer) :not(nav) div").all_text_contents()
    if not divs:
        divs = await page.locator("div").all_text_contents()
    filtered = await filter_texts(divs, keywords, EXCLUDE_TERMS)
    return filtered

async def main():
    urls = {
        "sales_specials": "https://www.stevenscreekchevy.com/newspecials.html",
        "service_specials": "https://www.stevenscreekchevy.com/service-parts-specials.html",
        "ev_incentives": "https://www.stevenscreekchevy.com/ev-incentives",
        "vehicle_inventory": "https://www.stevenscreekchevy.com/searchall.aspx",
        "financing_deals": "https://www.stevenscreekchevy.com/finance.aspx",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        dataset = {}
        for category, url in urls.items():
            print(f"Scraping {category} from {url} ...")
            keywords = PAGE_KEYWORDS.get(category, [])
            data = await scrape_filtered_divs(page, url, keywords)
            print(f"Found {len(data)} relevant text blocks in {category}\n")
            dataset[category] = data

        await browser.close()

        with open("2_stevenscreekchevy_dataset.json", "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        print("Dataset saved to stevenscreekchevy_dataset.json")

asyncio.run(main())
