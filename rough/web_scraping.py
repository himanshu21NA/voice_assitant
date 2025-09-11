# 
import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_sales_specials(page):
    await page.goto("https://www.stevenscreekchevy.com/newspecials.html", wait_until="load", timeout=300000)
    await page.wait_for_selector("div.offer-description, div.specials-content", timeout=300000)
    offers = await page.locator("div.offer-description, div.specials-content").all_text_contents()
    return offers

async def scrape_service_specials(page):
    await page.goto("https://www.stevenscreekchevy.com/service-parts-specials.html", wait_until="load", timeout=300000)
    await page.wait_for_selector("div.service-coupon, div.special-item", timeout=300000)
    specials = await page.locator("div.service-coupon, div.special-item").all_text_contents()
    return specials

async def scrape_ev_incentives(page):
    await page.goto("https://www.stevenscreekchevy.com/ev-incentives", wait_until="load", timeout=300000)
    await page.wait_for_selector("section#ev-incentives, div.rebate-info", timeout=300000)
    incentives = await page.locator("section#ev-incentives, div.rebate-info").all_text_contents()
    return incentives

async def scrape_vehicle_inventory(page):
    # Block images, stylesheet, fonts to speed loading
    await page.route("**/*", lambda route, request: route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_())

    await page.goto("https://www.stevenscreekchevy.com/searchnew.aspx", wait_until="load", timeout=300000)
    # Wait for inventory items container (adjust selector based on actual site)
    await page.wait_for_selector("div.inventory-list, div.inventory-item", timeout=300000)
    inventory_items = await page.locator("div.inventory-list div.inventory-item, div.inventory-item").all_text_contents()
    return inventory_items

async def scrape_financing_deals(page):
    await page.goto("https://www.stevenscreekchevy.com/finance.aspx", wait_until="load", timeout=300000)
    await page.wait_for_selector("section.finance-deals, div.offer-details, div.finance-info", timeout=300000)
    financing = await page.locator("section.finance-deals, div.offer-details, div.finance-info").all_text_contents()
    return financing

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        sales = await scrape_sales_specials(page)
        print("Sales Specials:", sales)

        service = await scrape_service_specials(page)
        print("Service Specials:", service)

        ev = await scrape_ev_incentives(page)
        print("EV Incentives:", ev)

        inventory = await scrape_vehicle_inventory(page)
        print("Vehicle Inventory:", inventory)

        financing = await scrape_financing_deals(page)
        print("Financing Deals:", financing)

        await browser.close()

asyncio.run(main())
