"""
Script to scrape today and tomorrow's badminton tournament matches
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List
from unidecode import unidecode
from playwright.async_api import Playwright, async_playwright

# Import shared functions
from script.get_match_html import (
    extract_tournament_name,
    fetch_match_html,
    fetch_all_dates_mode_max_round
)

DEFAULT_TOURNAMENT_LIST = [
    "https://bwfbadminton.com/tournament/5263/yonex-sunrise-bwf-world-junior-mixed-team-championships-2025",
    "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "https://bwfbadminton.com/tournament/5331/africa-para-badminton-championships-2025",
    "https://bwfbadminton.com/tournament/5408/victor-turkiye-international-challenge-2025",
    "https://bwfbadminton.com/tournament/5412/roketto-sydney-international-2025",
    "https://bwfbadminton.com/tournament/5522/algeria-international-2025"
]


def append_base_url(url: str, level: str, output_dir: str = "yesterday", country: str = "", city: str = "", timezone: str = "") -> None:
    """
    Append a base URL to today's JSON list file when today's tab exists
    
    Args:
        url: tournament URL to append
        level: tournament level to append
        output_dir: output directory path
        country: tournament country
        city: tournament city
        timezone: tournament IANA timezone
    """
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    filename = f"{date_str}_tournaments.json"
    filepath = os.path.join(output_dir, filename)
    
    # Load existing data or create new
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "date": date_str,
            "timestamp": today.isoformat(),
            "tournaments": []
        }
    tournament_name = extract_tournament_name(url)
    
    # Append URL if not already in list
    if tournament_name not in data["tournaments"]:
        data["tournaments"].append({
            "tournament_url": url,
            "level": level,
            "country": country,
            "city": city,
            "IANA_timezone": timezone
        })
    else:
        return
    data["last_updated"] = today.isoformat()

    # Save updated data
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return


async def scrape_tournament_for_dates(
    playwright: Playwright,
    url: str,
    tournament_name: str,
    level: str,
    dates: List[datetime],
    output_dir: str = "two_days",
    country: str = "",
    city: str = "",
    timezone: str = ""
) -> dict[str, str]:
    """
    Scrape tournament for multiple dates
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
        tournament_name: Tournament name
        level: Tournament level
        dates: List of dates to scrape
        output_dir: Output directory
        
    Returns:
        dict with date labels as keys and HTML as values
    """
    results = {}
    
    # Fetch mode_max_round by traversing all date tabs from first to last
    try:
        mode_max_round = await fetch_all_dates_mode_max_round(playwright, url)
        print(f"Found mode_max_round from all dates: {mode_max_round}")
    except Exception as e:
        print(f"Error fetching mode_max_round from all dates: {str(e)}")
        mode_max_round = {}
    
    # Fetch HTML for specified dates (today and tomorrow)
    for i, date in enumerate(dates):
        date_label = "today" if i == 0 else "tomorrow"
        
        try:
            html = await fetch_match_html(playwright, url, date)
            
            if html:
                results[date_label] = html
        except Exception as e:
            print(f"Error scraping {url} for {date_label}: {str(e)}")
    
    # Save the results
    if results:
        # Save HTML files
        # Use provided tournament_name if available, otherwise extract from URL
        tournament_name = extract_tournament_name(url, tournament_name)
        os.makedirs(output_dir, exist_ok=True)

        if "today" in results:
            today_file = os.path.join(output_dir, f"{tournament_name}_today.html")
            with open(today_file, "w", encoding="utf-8") as f:
                f.write(unidecode(results["today"]))
        
        if "tomorrow" in results:
            tomorrow_file = os.path.join(output_dir, f"{tournament_name}_tomorrow.html")
            with open(tomorrow_file, "w", encoding="utf-8") as f:
                f.write(unidecode(results["tomorrow"]))
        
        # Save round info
        from script.get_match_html import extract_league_id, format_tournament_name
        
        league_id = extract_league_id(url)
        league_name = format_tournament_name(tournament_name)
        age_category = "Juniors" if "junior" in level.lower() else "Adults"
        
        round_info = {
            "tournament_url": url,
            "league_id": league_id,
            "league_name": league_name,
            "level": level,
            "country": country,
            "city": city,
            "IANA_timezone": timezone,
            "age_category": age_category,
            "mode_max_round": mode_max_round,
            "timestamp": datetime.now().isoformat()
        }
        
        round_file = os.path.join(output_dir, f"{tournament_name}_round_info.json")
        with open(round_file, "w", encoding="utf-8") as f:
            json.dump(round_info, f, ensure_ascii=False, indent=2)
        
        # Record URL if today's data exists
        if "today" in results:
            append_base_url(url, level, "yesterday", country, city, timezone)
    
    return results


async def run(
    playwright: Playwright,
    url: str,
    level: str,
    output_dir: str = "two_days",
    country: str = "",
    city: str = "",
    timezone: str = "",
    tournament_name: str = ""
) -> None:
    """
    Main process for handling single tournament
    
    Args:
        playwright: Playwright instance
        url: tournament URL
        level: tournament level
        output_dir: output directory path
        country: tournament country
        city: tournament city
        timezone: tournament IANA timezone
        tournament_name: tournament name
    """
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    await scrape_tournament_for_dates(
        playwright,
        url,
        tournament_name,
        level,
        [today, tomorrow],
        output_dir,
        country,
        city,
        timezone
    )


async def main(
    playwright: Playwright,
    tournament_list: list[str] = None,
    tournament_name_list: list[str] = None,
    level_list: list[str] = None,
    country_list: list[str] = None,
    city_list: list[str] = None,
    timezone_list: list[str] = None,
    output_dir: str = "two_days"
) -> None:
    """
    Main program entry
    
    Args:
        playwright: Playwright instance
        tournament_list: tournament URL list, use default list if not provided
        tournament_name_list: tournament name list, use default list if not provided
        level_list: tournament level list, use default list if not provided
        country_list: tournament country list
        city_list: tournament city list
        timezone_list: tournament IANA timezone list
        output_dir: output directory path
    """
    if tournament_list is None:
        tournament_list = DEFAULT_TOURNAMENT_LIST
    
    if country_list is None:
        country_list = [""] * len(tournament_list)
    if city_list is None:
        city_list = [""] * len(tournament_list)
    if timezone_list is None:
        timezone_list = [""] * len(tournament_list)

    for i, url in enumerate(tournament_list):
        await run(
            playwright, 
            url, 
            level_list[i],
            output_dir,
            country_list[i],
            city_list[i],
            timezone_list[i],
            tournament_name_list[i] if tournament_name_list else ""
        )


if __name__ == "__main__":
    async def entry():
        async with async_playwright() as playwright:
            await main(playwright, DEFAULT_TOURNAMENT_LIST, "two_days")

    asyncio.run(entry())
