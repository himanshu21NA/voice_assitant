# # 
# import asyncio
# from playwright.async_api import async_playwright

# async def test_fs_div_all():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         page = await browser.new_page()
#         await page.goto("https://www.stevenscreekchevy.com/newspecials.html", wait_until="domcontentloaded", timeout=120000)
        
#         # Wait longer to allow JS populate content
#         await asyncio.sleep(10)
        
#         content = await page.locator("#fs_div_all").text_content()
#         print("Content inside #fs_div_all:", content)

#         await page.screenshot(path="fs_div_all_debug.png")
#         await browser.close()

# asyncio.run(test_fs_div_all())

import asyncio
from playwright.async_api import async_playwright

async def test_news_specials():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto("https://www.stevenscreekchevy.com/newspecials.html", wait_until="domcontentloaded", timeout=120000)
            await asyncio.sleep(10)  # allow some time for JS async content
            content = await page.content()
            print("Page content length:", len(content))
            with open("content.txt", "w", encoding="utf-8") as f:
                f.write(content)
            await page.screenshot(path="news_specials_loaded.png")
        except Exception as e:
            print("Error loading page:", e)
        await browser.close()

asyncio.run(test_news_specials())
