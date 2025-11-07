"""
Script to scrape yesterday's badminton tournament matches
Reads tournament list from yesterday's JSON file and scrapes only yesterday's matches
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from playwright.async_api import Playwright, async_playwright

# Import shared functions
from script.get_match_html import (
    fetch_match_html,
    find_mode_max_round,
    save_match_data
)


def load_yesterday_tournaments(yesterday_dir: str = "yesterday") -> List[Dict[str, str]]:
    """
    Load yesterday's tournament list from JSON file
    
    Args:
        yesterday_dir: Directory containing yesterday's tournament JSON
        
    Returns:
        List of tournament dicts with 'tournament_url' and 'level'
    """
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    filename = f"{date_str}_tournaments.json"
    filepath = os.path.join(yesterday_dir, filename)
    
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("tournaments", [])


async def scrape_match_by_date(
    playwright: Playwright,
    url: str,
    level: str,
    target_date: datetime,
    output_dir: str = "date_matches",
    country: str = "",
    city: str = "",
    timezone: str = ""
) -> bool:
    """
    Scrape match for a single tournament on a specific date
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
        level: Tournament level
        target_date: Target date to scrape
        output_dir: Output directory
        country: Tournament country
        city: Tournament city
        timezone: Tournament IANA timezone
        
    Returns:
        True if successfully scraped, False otherwise
    """
    try:
        html = await fetch_match_html(playwright, url, target_date)
        
        if html:
            mode_max_round = find_mode_max_round(html)
            
            # Check if output_dir is yesterday/leagues - if so, don't use suffix
            use_suffix = "yesterday/leagues" not in output_dir.replace("\\", "/")
            
            save_match_data(url, level, html, mode_max_round, target_date, output_dir, use_suffix, country, city, timezone)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return False


async def main_by_date(
    playwright: Playwright,
    target_date: datetime,
    tournament_list: List[Dict[str, str]],
    output_dir: str = "date_matches"
) -> None:
    """
    Main function to scrape matches for a specific date
    
    Args:
        playwright: Playwright instance
        target_date: Target date to scrape
        tournament_list: List of tournaments with url and level
        output_dir: Output directory for scraped HTML and info
    """
    if not tournament_list:
        print("No tournaments provided")
        return
    
    print(f"Found {len(tournament_list)} tournaments to scrape for {target_date.strftime('%Y-%m-%d')}")
    
    for tournament in tournament_list:
        url = tournament.get("tournament_url")
        level = tournament.get("level", "")
        country = tournament.get("country", "")
        city = tournament.get("city", "")
        timezone = tournament.get("IANA_timezone", "")
        
        if not url:
            continue
        
        print(f"Scraping: {url}")
        success = await scrape_match_by_date(playwright, url, level, target_date, output_dir, country, city, timezone)
        
        if success:
            print(f"✓ Successfully scraped: {url}")
        else:
            print(f"✗ Failed to scrape: {url}")


async def main(
    playwright: Playwright,
    output_dir: str = "yesterday/leagues",
    yesterday_dir: str = "yesterday"
) -> None:
    """
    Main function to scrape yesterday's matches
    
    Args:
        playwright: Playwright instance
        output_dir: Output directory for scraped HTML and info
        yesterday_dir: Directory containing yesterday's tournament list JSON
    """
    tournaments = load_yesterday_tournaments(yesterday_dir)
    
    if not tournaments:
        print("No tournaments found for yesterday")
        return
    
    yesterday = datetime.now() - timedelta(days=1)
    
    await main_by_date(playwright, yesterday, tournaments, output_dir)


if __name__ == "__main__":
    async def entry():
        async with async_playwright() as playwright:
            await main(playwright, "yesterday/leagues", "yesterday")
    
    asyncio.run(entry())
