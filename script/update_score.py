import asyncio
from playwright.async_api import async_playwright, Playwright
import json
from typing import Optional
from datetime import datetime
from script.get_match_html import is_bwfworldtour_url, initialize_page, create_browser_context, find_date_tab_index, switch_to_list_view, get_date_tabs, extract_league_id
import time
from fastapi import HTTPException
import httpx

class PlaywrightManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.should_stop = False
        self.webhook_url = "https://ds.n8n.poc.owgps.net/webhook-test/phase2/playwright"
    
    async def send_to_n8n(self, data):
        async with httpx.AsyncClient() as client:
            await client.post(self.webhook_url, json=data)
    
    async def fetch_response_by_url(self, playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
        """Fetch Web response for regular site using goint to the specific date url"""
        try:
            result = []
            async def log_response(response):
                if (response.url == api_url):
                    result.append(await response.json())

            self.page.on("response", log_response)

            target_url = get_date_url(url, target_date)

            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
            await initialize_page(self.page)
            await self.page.wait_for_timeout(2500)

            return result[0]

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Scraping failed: {str(e)}"
            )

    async def fetch_response_by_tab(self, playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
        """Fetch Web response for regular site using tab clicks with specific date"""
        try:
            result = []
            async def log_response(response):
                if (response.url == api_url):
                    result.append(await response.json())

            self.page.on("response", log_response)

            await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await initialize_page(self.page)
            
            total_dates, all_date_buttons, is_li_format = await get_date_tabs(self.page)
        
            if total_dates == 0:
                return None
            
            date_tab_texts = []
            for i in range(total_dates):
                try:
                    element = all_date_buttons.nth(i)
                    key = await element.inner_text()
                    date_tab_texts.append(key.strip())
                except Exception:
                    date_tab_texts.append("")

            target_date_index = find_date_tab_index(date_tab_texts, target_date)
            
            if target_date_index is None:
                return None
            
            button = all_date_buttons.nth(target_date_index)
            await button.click(force=True)
            await self.page.wait_for_timeout(2500)
            await switch_to_list_view(self.page)

            return result[0]

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Scraping failed: {str(e)}"
            )

    async def fetch_match_response(self, playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
        """
        Fetch match Web response for a specific date (automatically chooses method based on URL)
        
        Args:
            playwright: Playwright instance
            url: Tournament URL
            target_date: Target date to scrape
            api_url: Target response api url
            
        Returns:
            Matches information or None if not found
        """

        is_worldtour = is_bwfworldtour_url(url)
        if is_worldtour:
            return await self.fetch_response_by_url(playwright, url, target_date, api_url)
        else:
            return await self.fetch_response_by_tab(playwright, url, target_date, api_url)

    async def start(self, tournament_url, date, api_url, feq):
        async with async_playwright() as playwright:
            self.browser, self.context, self.page = await create_browser_context(playwright)

            try:
                while not self.should_stop:
                    print(f"start to monitor.")
                    result = await self.fetch_match_response(playwright, tournament_url, date, api_url)

                    league_id = extract_league_id(tournament_url)
                    matches  = []

                    if result:
                        for match_item in result:
                            try:
                                single_match = MatchData()
                                single_match.update_league_id(league_id)
                                single_match.update(match_item)
                                matches.append(single_match.to_dict())
                            except:
                                pass

                    await self.send_to_n8n(matches)

                    # if result:
                    #     with open(f"{date}.json", "a", encoding="utf-8") as f:
                    #         data = json.dump(result, f, indent=2, ensure_ascii=False)

                    print(f"start to sleep.")
                    
                    await asyncio.sleep(feq)
            except asyncio.CancelledError:
                print(f"The task is canceled.")

            finally:
                await self.context.close()
                await self.browser.close()
                print(f"Close the playwright.")
                self.should_stop = False

    def stop(self):
        self.should_stop = True

class MatchData:
    def __init__(self):
        self.match_id = None
        self.game_1_home_score = None
        self.game_1_away_score = None
        self.game_2_home_score = None
        self.game_2_away_score = None
        self.game_3_home_score = None
        self.game_3_away_score = None
        self.kickoff_time = ""

    def update_league_id(self, league_id: str):
        self.league_id = int(league_id)
    
    def update(self, match_item):
        self.match_id = int(match_item["id"])
        
        # score
        for idx, score_item in enumerate(match_item["score"], 1):
            home_score = f"game_{score_item['set']}_home_score"
            away_score = f"game_{score_item['set']}_away_score"
            setattr(self, home_score, score_item["home"])
            setattr(self, away_score, score_item["away"])
        
        self.kickoff_time = match_item["matchTimeUtc"]
    
    def to_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)
        
    def to_dict(self):
        data = self.__dict__.copy()
        return data



async def monitor_bwf_matches(manager, tournament_code, tournament_url, date, feq):
    formatted_date = date.strftime("%Y-%m-%d")
    api_url = f"https://extranet-lv.bwfbadminton.com/api/tournaments/day-matches?tournamentCode={tournament_code}&date={formatted_date}&order=2&court=0"

    await manager.start(tournament_url, date, api_url, feq)


if __name__ == "__main__":
    async def main():
        # input
        tmt_code = "5789F115-C018-47E2-81B0-7CA2DC3F5CA8"
        tmt_url = "https://bwfworldtour.bwfbadminton.com/tournament/5199/sathio-group-australian-open-2025/results/"
        # tmt_code = "4908E48F-CF45-4ED0-BC7B-3A65EBC1B785"
        # tmt_url = "https://bwfbadminton.com/tournament/5721/badminton-asia-west-asia-regional-championships-2025-individual"
        date = "2025-11-20"
        dt = datetime.strptime(date, "%Y-%m-%d")
        feq = 900 # 15mins

        manager = PlaywrightManager()
        result = await monitor_bwf_matches(manager, tmt_code, tmt_url, dt, feq)

        if result:
            with open(f"{tmt_code}.json", "w", encoding="utf-8") as f:
                data = json.dump(result, f, indent=2, ensure_ascii=False)

    asyncio.run(main())