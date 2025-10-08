import math
import re
import os
import shutil
import asyncio
from playwright.async_api import Playwright, async_playwright


async def run(playwright: Playwright) -> None:
    """Scrape this week's tournament list"""
    print("Scraping this week tournaments...")
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US'
    )
    page = await context.new_page()
    # Hide webdriver features
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    await page.goto("https://bwfbadminton.com/calendar/", wait_until="domcontentloaded", timeout=30000)
    await page.get_by_role("button", name="Close").click(timeout=5000)
    await page.get_by_role("link", name="THIS WEEK").click()
    await page.wait_for_timeout(3000)
    if await page.locator("text=0 EVENTS").count() > 0:
        print("THIS WEEK no events found. Exiting...")
        await context.close()
        await browser.close()
        return

    await page.wait_for_selector(".calendar-content-wrapper")
    events_text = await page.locator("div:has-text('THIS WEEK')").nth(0).inner_text()
    total_events = re.search(r"THIS WEEK\s+(\d+)\s+EVENTS", events_text).group(1)
    total_events = int(total_events)
    total_pages = math.ceil(total_events / 10)
    print(f"Found {total_events} events, {total_pages} pages")

    for i in range(total_pages):
        await page.wait_for_timeout(2000)  # Wait for page to stabilize
        await page.wait_for_selector(".calendar-content-wrapper")
        html = await page.locator(".calendar-content-wrapper").evaluate("el => el.outerHTML")

        with open(f"this_week/page_{i+1}.html", "w", encoding="utf-8") as f:
            f.write(html)

        print(f"this_week/page_{i+1}.html saved")

        if i < total_pages - 1:
            await page.get_by_role("navigation").filter(has_text=f"Page {str(i+1)} of").locator("a").nth(2).click()

    await context.close()
    await browser.close()

if __name__ == "__main__":
    async def main():
        folder = "this_week"
        if os.path.exists(folder):
            print(f"Removing {folder}...")
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())
