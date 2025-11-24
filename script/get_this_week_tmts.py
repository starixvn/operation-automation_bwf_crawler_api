import json
import re
import math
import asyncio
from playwright.async_api import Playwright, async_playwright
from script.get_match_html import create_browser_context, close_popup_if_exists
from schema import ThisWeekTournamentListItem 


async def get_this_week_tournament_list(playwright: Playwright, enter_url: str, target_url: str) -> list[dict]:
    """Listen to response and return the results"""
    results = []
    browser, context, page = await create_browser_context(playwright)
    
    async def log_response(response):
        if response.url == target_url:
            try:
                json_data = await response.json()
                results.append(json_data)
            except Exception as e:
                print(f"Error parsing JSON response: {e}")
                try:
                    text_data = await response.text()
                    print(f"Response text: {text_data[:200]}...")  # Print first 200 chars
                    results.append(text_data)
                except Exception as e2:
                    print(f"Error reading response text: {e2}")

    try:
        # Register response listener - Playwright automatically handles async callbacks
        page.on("response", log_response)
        print(f"Navigating to {enter_url}")
        await page.goto(enter_url, wait_until="domcontentloaded", timeout=10000)
        await close_popup_if_exists(page)

        await page.get_by_role("link", name="THIS WEEK").click()
        await page.wait_for_timeout(3000)
        # Use regex to match exactly "0 EVENTS" (not "10 EVENTS", "20 EVENTS", etc.)
        if await page.locator("text=/^0 EVENTS$/").count() > 0:
            print("THIS WEEK no events found. Exiting...")
            await context.close()
            await browser.close()
            return []

        await page.wait_for_selector(".calendar-content-wrapper")
        events_text = await page.locator("div:has-text('THIS WEEK')").nth(0).inner_text()
        total_events = re.search(r"THIS WEEK\s+(\d+)\s+EVENTS", events_text).group(1)
        total_events = int(total_events)
        total_pages = math.ceil(total_events / 10)
        print(f"Found {total_events} events, {total_pages} pages")

        for i in range(total_pages):
            print(f"Getting page {i+1} of {total_pages}")
            await page.wait_for_timeout(2000)  # Wait for page to stabilize

            if i < total_pages - 1:
                await page.get_by_role("navigation").filter(has_text=f"Page {str(i+1)} of").locator("a").nth(2).click()
                print(f"Clicked next page")

    except Exception as e:
        print(f"Error navigating to {enter_url}: {e}")
        return []
    finally:
        await context.close()
        await browser.close()


    return results

def parse_tournament_data(data: list[dict]) -> list[ThisWeekTournamentListItem]:
    tournament_items = []
    print("dataaaa", data)

    # Process tournaments
    for tmt in data:
        tournament_items.append(ThisWeekTournamentListItem(
            tmt_id=tmt.get("id", tmt.get("tmt_id", 0)),
            tmt_code=tmt.get("code", tmt.get("tmt_code", "")),
            tmt_url=tmt.get("url", tmt.get("tmt_url", "")),
            tmt_name=tmt.get("name", tmt.get("tmt_name", "")),
            tmt_level=tmt.get("category", "")
        ))
    
    return tournament_items

async def main():
    enter_url = "https://bwfbadminton.com/calendar/"
    target_url = "https://extranet-lv.bwfbadminton.com/api/vue-tournaments-search"
    results = []
    async with async_playwright() as playwright:
        tmts = await get_this_week_tournament_list(playwright, enter_url, target_url)
        if len(tmts) == 0:
            return []

        for page in tmts:
            if "results" in page and "data" in page["results"]:
                parsed_items = parse_tournament_data(page["results"]["data"])
                results.extend(parsed_items)
        return results

if __name__ == "__main__":
    asyncio.run(main())
