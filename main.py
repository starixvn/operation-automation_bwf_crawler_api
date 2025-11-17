"""
Badminton Tournament Scraper API

Provides three main endpoints:
1. /this-week-tournaments - Get this week's tournament list
2. /two-days-matches - Get today and tomorrow schedules for specified tournaments
3. /yesterday-matches - Get yesterday's matches from yesterday's tournament list
"""

from fastapi import FastAPI, HTTPException
import os
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

from script.get_this_week_tournament_html import run as run_this_week
from script.get_two_days_match_html import main as run_two_days
from script.get_yesterday_match_html import main_by_date, load_yesterday_tournaments
from script.tournament_loader import load_tournament_files, build_tournament_list
from script.tournament_filter import filter_tournaments
from schema import (
    TournamentRequest, DateTournamentRequest, 
    ScrapeResponse, TwoDaysResponse, TournamentListResponse, TournamentListItem
)
from utils import clear_directory, delete_file, setup_logger

# Setup logger
logger = setup_logger("main", "api.log")

app = FastAPI(
    title="Badminton Tournament Scraper API",
    description="API for scraping badminton tournament schedules",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("Starting Badminton Tournament Scraper API")
    logger.info("Version: 1.0.0")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("Shutting down Badminton Tournament Scraper API")


@app.get("/")
async def root():
    """API root path"""
    return {
        "message": "Badminton Tournament Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "this_week": "/this-week-tournaments",
            "two_days": "/two-days-matches",
            "yesterday_tournaments": "/yesterday-tournaments",
            "matches_by_date": "/matches-by-date"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/this-week-tournaments", response_model=ScrapeResponse)
async def scrape_this_week_tournaments():
    """
    Scrape this week's tournament list

    Synchronous execution, return result when complete
    """
    import time
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting this week tournaments scraping")
    
    try:
        folder = "this_week"
        clear_directory(folder)
        logger.info(f"Cleared output directory: {folder}")

        async with async_playwright() as playwright:
            logger.info("Launching browser for scraping")
            await run_this_week(playwright)

        files = {}
        for filename in os.listdir(folder):
            if filename.endswith('.html'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    files[filename] = html_content
                    file_size = len(html_content)
                    logger.info(f"Scraped file: {filename} (size: {file_size:,} bytes)")

        elapsed_time = time.time() - start_time
        logger.info(f"Successfully scraped {len(files)} tournament files in {elapsed_time:.2f}s")
        logger.info("=" * 60)
        
        return ScrapeResponse(
            status="success",
            message=f"Successfully scraped this week's tournaments, total {len(files)}  files",
            timestamp=datetime.now().isoformat(),
            output_dir=folder,
            files=files
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"This week tournaments scraping failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@app.post("/two-days-matches", response_model=TwoDaysResponse)
async def scrape_two_days_matches(request: TournamentRequest):
    """
    Scrape today and tomorrow schedules for specified tournaments

    Parameters:
    - tournaments: List of tournament objects with tournament_name, url and level
        - tournament_name: Tournament name
        - url: Tournament URL
        - level: Tournament level/category
    - output_dir: Output directory (default: two_days)

    Excluded tournaments:
    - Empty level
    - Level contains "para"
    - International Series
    - International Challenge
    - Junior International Series
    - Junior Tournament

    Returns:
    - TwoDaysResponse with tournament data including league_id, league_name, and schedules
    """
    if not request.tournaments:
        logger.warning("Two days matches request with no tournaments")
        raise HTTPException(status_code=400, detail="At least one tournament is required")

    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Starting two days matches scraping for {len(request.tournaments)} tournaments")
    
    try:
        # Filter tournaments
        valid_tournaments, excluded_count = filter_tournaments(request.tournaments)
        
        if excluded_count > 0:
            logger.info(f"Excluded {excluded_count} tournament(s) based on level filters")
        
        if not valid_tournaments:
            logger.warning("No valid tournaments after filtering")
            return TwoDaysResponse(
                status="success",
                message="No tournaments to scrape after filtering",
                tournaments=[]
            )
        
        # Prepare and scrape (no longer clear directory at start)
        os.makedirs(request.output_dir, exist_ok=True)

        url_strings = [str(t.url) for t in valid_tournaments]
        tournament_name_strings = [t.tournament_name for t in valid_tournaments]
        level_strings = [t.level for t in valid_tournaments]
        country_strings = [t.country for t in valid_tournaments]
        city_strings = [t.city for t in valid_tournaments]
        timezone_strings = [t.IANA_timezone for t in valid_tournaments]
        logger.info(f"Queued {len(url_strings)} tournament(s) for scraping")
        
        logger.info("Launching browser for scraping")
        async with async_playwright() as playwright:
            await run_two_days(
                playwright, 
                tournament_list=url_strings, 
                tournament_name_list=tournament_name_strings,
                level_list=level_strings,
                country_list=country_strings,
                city_list=city_strings,
                timezone_list=timezone_strings,
                output_dir=request.output_dir
            )

        # Load and process files
        logger.info("Processing scraped files")
        tournaments_data = load_tournament_files(request.output_dir, logger)
        tournaments = build_tournament_list(tournaments_data, logger)

        # Clean up: delete files for this batch after processing
        logger.info("Cleaning up processed tournament files")
        for tournament_name in tournaments_data.keys():
            # Delete HTML files
            today_file = os.path.join(request.output_dir, f"{tournament_name}_today.html")
            tomorrow_file = os.path.join(request.output_dir, f"{tournament_name}_tomorrow.html")
            round_info_file = os.path.join(request.output_dir, f"{tournament_name}_round_info.json")
            
            for file_path in [today_file, tomorrow_file, round_info_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Deleted: {file_path}")
        
        logger.info(f"Cleaned up {len(tournaments_data)} tournament file sets")

        # Log success
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully scraped two days matches for {len(tournaments)} tournaments in {elapsed_time:.2f}s")
        logger.info("=" * 60)
        
        return TwoDaysResponse(
            status="success",
            message=f"Successfully scraped today and tomorrow schedules for {len(tournaments)} tournaments",
            tournaments=tournaments
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Two days matches scraping failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@app.get("/yesterday-tournaments", response_model=TournamentListResponse)
async def get_yesterday_tournaments():
    """
    Get yesterday's tournament list
    
    This endpoint reads yesterday's tournament list from yesterday/YYYY-MM-DD_tournaments.json
    The JSON file is determined by today's date. For example:
    - If today is 2025-10-29, it will read yesterday/2025-10-28_tournaments.json
    
    Returns:
    - TournamentListResponse with list of tournaments (without HTML)
    """
    logger.info("Getting yesterday's tournament list")
    
    try:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date_str = yesterday.strftime("%Y-%m-%d")
        yesterday_json = os.path.join("yesterday", f"{yesterday_date_str}_tournaments.json")
        
        # Check if yesterday's tournament file exists
        if not os.path.exists(yesterday_json):
            logger.warning(f"Yesterday's tournament file not found: {yesterday_json}")
            return TournamentListResponse(
                status="success",
                message=f"No tournament list found for {yesterday_date_str}",
                date=yesterday_date_str,
                tournaments=[]
            )
        
        # Read tournaments
        tournaments = load_yesterday_tournaments("yesterday")
        logger.info(f"Found {len(tournaments)} tournaments for {yesterday_date_str}")
        
        # Convert to response format
        tournament_items = [
            TournamentListItem(
                tournament_url=t.get("tournament_url", ""),
                level=t.get("level", ""),
                country=t.get("country", ""),
                city=t.get("city", ""),
                IANA_timezone=t.get("IANA_timezone", "")
            )
            for t in tournaments
        ]
        
        return TournamentListResponse(
            status="success",
            message=f"Successfully loaded {len(tournament_items)} tournaments for {yesterday_date_str}",
            date=yesterday_date_str,
            tournaments=tournament_items
        )
    
    except Exception as e:
        logger.error(f"Failed to get yesterday's tournaments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load tournaments: {str(e)}"
        )


@app.post("/matches-by-date", response_model=TwoDaysResponse)
async def scrape_matches_by_date(request: DateTournamentRequest):
    """
    Scrape matches for specified date and tournaments
    
    Parameters:
    - date: Target date (format: YYYY-MM-DD, e.g., "2025-10-28")
    - tournaments: List of tournament objects with url and level
        - url: Tournament URL
        - level: Tournament level/category
    - output_dir: Output directory (default: yesterday/leagues)
    
    Note: Files in yesterday/leagues directory will be saved without date suffix (e.g., tournament-name.html)
    
    Returns:
    - TwoDaysResponse with tournament data including league_id, league_name, and match HTML
    """
    if not request.tournaments:
        logger.warning("Scrape by date request with no tournaments")
        raise HTTPException(status_code=400, detail="At least one tournament is required")
    
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Starting scraping for date {request.date} with {len(request.tournaments)} tournaments")
    
    try:
        # Parse date
        try:
            target_date = datetime.strptime(request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Clear output directory
        clear_directory(request.output_dir)
        logger.info(f"Cleared output directory: {request.output_dir}")
        
        # Convert tournaments to dict format
        tournament_list = [
            {
                "tournament_url": str(t.url),
                "level": t.level
            }
            for t in request.tournaments
        ]
        
        logger.info(f"Queued {len(tournament_list)} tournament(s) for scraping on {request.date}")
        logger.info("Launching browser for scraping")
        
        # Run scraper
        async with async_playwright() as playwright:
            await main_by_date(
                playwright, 
                target_date=target_date,
                tournament_list=tournament_list,
                output_dir=request.output_dir
            )
        
        # Load and process files
        logger.info("Processing scraped files")
        tournaments_data = load_tournament_files(request.output_dir, logger)
        tournaments = build_tournament_list(tournaments_data, logger)
        
        # Log success
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully scraped matches for {len(tournaments)} tournaments on {request.date} in {elapsed_time:.2f}s")
        logger.info("=" * 60)
        
        return TwoDaysResponse(
            status="success",
            message=f"Successfully scraped matches for {len(tournaments)} tournaments on {request.date}",
            tournaments=tournaments
        )
    
    except HTTPException:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Scraping by date failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=600)
