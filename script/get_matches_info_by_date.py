import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
from script.get_match_html import fetch_match_response, extract_league_id
import time

class MatchData:
    def __init__(self):
        self.league_id = None
        self.match_id = None
        self.player_home_1_id = None
        self.player_home_1_country = ""
        self.player_home_1_name = ""
        self.player_home_2_id = None
        self.player_home_2_country = ""
        self.player_home_2_name = ""
        self.player_away_1_id = None
        self.player_away_1_country = ""
        self.player_away_1_name = ""
        self.player_away_2_id = None
        self.player_away_2_country = ""
        self.player_away_2_name = ""
        self.mode = ""
        self.round = ""
        self.court = ""
        self.kickoff_time = ""

    def update_league_id(self, league_id: str):
        self.league_id = int(league_id)
    
    def update(self, match_item):
        self.match_id = int(match_item["id"])
        
        # players
        for idx, home_player in enumerate(match_item["team1"]["players"], 1):
            if idx == 1:
                self.player_home_1_id = int(home_player["id"])
                self.player_home_1_country = home_player["countryCode"]
                self.player_home_1_name = home_player["nameDisplay"]
            elif idx == 2:
                self.player_home_2_id = int(home_player["id"])
                self.player_home_2_country = home_player["countryCode"]
                self.player_home_2_name = home_player["nameDisplay"]
        
        for idx, away_player in enumerate(match_item["team2"]["players"], 1):
            if idx == 1:
                self.player_away_1_id = int(away_player["id"])
                self.player_away_1_country = away_player["countryCode"]
                self.player_away_1_name = away_player["nameDisplay"]
            elif idx == 2:
                self.player_away_2_id = int(away_player["id"])
                self.player_away_2_country = away_player["countryCode"]
                self.player_away_2_name = away_player["nameDisplay"]

        self.mode = match_item["drawName"]
        self.round = match_item["roundName"]
        self.court = match_item["courtName"]
        self.kickoff_time = match_item["matchTimeUtc"]
    
    def to_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)
        
    def to_dict(self):
        data = self.__dict__.copy()
        return data



async def fetch_bwf_matches(tournament_code, tournament_url, date):
    formatted_date = date.strftime("%Y-%m-%d")
    api_url = f"https://extranet-lv.bwfbadminton.com/api/tournaments/day-matches?tournamentCode={tournament_code}&date={formatted_date}&order=2&court=0"

    async with async_playwright() as playwright:
        result = await fetch_match_response(playwright, tournament_url, date, api_url)

    league_id = extract_league_id(tournament_url)

    matches  = []
    errors = 0

    if result:
        for match_item in result:
            try:
                single_match = MatchData()
                single_match.update_league_id(league_id)
                single_match.update(match_item)
                matches.append(single_match.to_dict())
            except:
                errors += 1
                pass

    return matches, errors

if __name__ == "__main__":
    async def main():
        # input
        tmt_code = "5789F115-C018-47E2-81B0-7CA2DC3F5CA8"
        tmt_url = "https://bwfworldtour.bwfbadminton.com/tournament/5199/sathio-group-australian-open-2025/results/"
        # tmt_code = "4908E48F-CF45-4ED0-BC7B-3A65EBC1B785"
        # tmt_url = "https://bwfbadminton.com/tournament/5721/badminton-asia-west-asia-regional-championships-2025-individual"
        date = "2025-11-20"
        dt = datetime.strptime(date, "%Y-%m-%d")

        result = await fetch_bwf_matches(tmt_code, tmt_url, dt)

        if result:
            with open(f"{tmt_code}.json", "w", encoding="utf-8") as f:
                data = json.dump(result, f, indent=2, ensure_ascii=False)

    asyncio.run(main())