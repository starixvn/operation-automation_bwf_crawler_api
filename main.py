"""
Badminton Tournament Scraper API

Provides two main endpoints:
1. /this-week-tournaments - Get this week's tournament list
2. /two-days-matches - Get today and tomorrow schedules for specified tournaments
"""

from fastapi import FastAPI, HTTPException
from typing import Optional
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

from script.get_this_week_tournament_html import run as run_this_week
from script.get_two_days_match_html import main as run_two_days
from script.tournament_loader import load_tournament_files, build_tournament_list
from schema import TournamentRequest, ScrapeResponse, TwoDaysResponse
from utils import clear_directory, setup_logger

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
            "two_days": "/two-days-matches"
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
    - urls: Tournament URL list
    - output_dir: Output directory (default: two_days)

    Returns:
    - TwoDaysResponse with tournament data including league_id, league_name, and schedules
    """
    if not request.urls:
        logger.warning("Two days matches request with no URLs")
        raise HTTPException(status_code=400, detail="At least one URL is required")

    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Starting two days matches scraping for {len(request.urls)} tournaments")
    
    try:
        # Prepare and scrape
        clear_directory(request.output_dir)
        logger.info(f"Cleared output directory: {request.output_dir}")

        url_strings = [str(url) for url in request.urls]
        logger.info(f"Queued {len(url_strings)} tournament(s)")
        
        logger.info("Launching browser for scraping")
        async with async_playwright() as playwright:
            await run_two_days(playwright, tournament_list=url_strings, output_dir=request.output_dir)

        # Load and process files
        logger.info("Processing scraped files")
        tournaments_data = load_tournament_files(request.output_dir, logger)
        tournaments = build_tournament_list(tournaments_data, logger)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=600)
