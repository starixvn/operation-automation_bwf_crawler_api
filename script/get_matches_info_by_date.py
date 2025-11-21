import asyncio
from playwright.async_api import async_playwright
import time,json


async def fetch_bwf_matches(tournament_code, date):
    api_url = f"https://extranet-lv.bwfbadminton.com/api/tournaments/day-matches?tournamentCode={tournament_code}&date={date}&order=2&court=0"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        page = await context.new_page()
        result = []

        # 🔎 加上監聽，印出所有 request header
        # async def log_request(request):
        #     print("\n==== 🔵 Request ====")
        #     print("URL:", request.url)
        #     print("Method:", request.method)
        #     print("Headers:", request.headers)
        
        async def log_response(response):
            # print("\n==== 🟢 Response ====")
            # print("URL:", response.url)
            # print("Status:", response.status)
            # print("Headers:", response.headers)
            if (response.url == api_url):
                # print(response.text())
                result.append(await response.text())

        # page.on("request", log_request)
        page.on("response", log_response)

        print("🔍 Visiting website to bypass Cloudflare...")
        await page.goto("https://bwfworldtour.bwfbadminton.com/tournament/5199/sathio-group-australian-open-2025/results/", wait_until="domcontentloaded")
        time.sleep(3)
        await page.get_by_role("button", name="Close").click()

        return result

if __name__ == "__main__":
    async def main():
        tmt_code = "5789F115-C018-47E2-81B0-7CA2DC3F5CA8"
        date = "2025-11-21"
        result = await fetch_bwf_matches(tmt_code, date)

        if result:
            print(result)
            # print(json.dumps(result, indent=2, ensure_ascii=False))
        # async with async_playwright() as playwright:
        #     await run(playwright)

    asyncio.run(main())