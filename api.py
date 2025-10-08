"""
Badminton Tournament Scraper API

Provides two main endpoints:
1. /this-week-tournaments - Get this week's tournament list
2. /two-days-matches - Get today and tomorrow schedules for specified tournaments
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import os
from datetime import datetime
import shutil
import gzip
import base64
from playwright.async_api import async_playwright
from get_this_week_tournament_html import run as run_this_week
from get_two_days_match_html import main as run_two_days


def clear_directory(directory: str) -> None:
    """Clear all contents of a directory without deleting the directory itself"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def compress_html(html_content: str) -> dict:
    """Compress HTML content with gzip and base64 encode"""
    compressed = gzip.compress(html_content.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('ascii')
    return {
        "compressed": True,
        "data": encoded
    }


app = FastAPI(
    title="Badminton Tournament Scraper API",
    description="API for scraping badminton tournament schedules",
    version="1.0.0"
)


class TournamentRequest(BaseModel):
    """Tournament request model"""
    urls: List[HttpUrl]
    output_dir: Optional[str] = "two_days"


class TournamentData(BaseModel):
    """Single tournament data"""
    tournament_url: str
    tournament_name: str
    max_round: Optional[str] = None  # Format: "R32", "R64" etc
    today_html: Optional[dict] = None  # {"compressed": true, "data": "..."}
    tomorrow_html: Optional[dict] = None


class ScrapeResponse(BaseModel):
    """Scraper response model"""
    status: str  # success, failed
    message: str
    timestamp: str
    output_dir: Optional[str] = None
    files: Optional[dict] = None  # Filename to HTML content mapping


class TwoDaysResponse(BaseModel):
    """Two-days schedule response model"""
    status: str
    message: str
    tournaments: List[TournamentData]


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
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/this-week-tournaments", response_model=ScrapeResponse)
async def scrape_this_week_tournaments():
    """
    Scrape this week's tournament list

    Synchronous execution, return result when complete
    """
    print("Scraping this week tournaments...")
    try:
        folder = "this_week"
        clear_directory(folder)

        async with async_playwright() as playwright:
            await run_this_week(playwright)

        files = {}
        for filename in os.listdir(folder):
            if filename.endswith('.html'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    files[filename] = compress_html(html_content)

        return ScrapeResponse(
            status="success",
            message=f"Successfully scraped this week's tournaments, total {len(files)}  files",
            timestamp=datetime.now().isoformat(),
            output_dir=folder,
            files=files
        )

    except Exception as e:
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

    Synchronous execution, return result when complete
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="At least one URL is required")

    try:
        folder = request.output_dir
        clear_directory(folder)

        url_strings = [str(url) for url in request.urls]
        url_to_name = {}
        for url in url_strings:
            tournament_name = url.rstrip('/').split('/')[-1]
            url_to_name[tournament_name] = url

        async with async_playwright() as playwright:
            await run_two_days(playwright, tournament_list=url_strings, output_dir=request.output_dir)

        import json
        tournaments_data = {}

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if filename.endswith('_today.html'):
                tournament_name = filename.replace('_today.html', '')
                if tournament_name not in tournaments_data:
                    tournaments_data[tournament_name] = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    tournaments_data[tournament_name]['today_html'] = compress_html(html_content)

            elif filename.endswith('_tomorrow.html'):
                tournament_name = filename.replace('_tomorrow.html', '')
                if tournament_name not in tournaments_data:
                    tournaments_data[tournament_name] = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    tournaments_data[tournament_name]['tomorrow_html'] = compress_html(html_content)

            elif filename.endswith('_round_info.json'):
                tournament_name = filename.replace('_round_info.json', '')
                if tournament_name not in tournaments_data:
                    tournaments_data[tournament_name] = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if 'max_round' in json_data:
                        max_round_num = json_data['max_round']
                        tournaments_data[tournament_name]['max_round'] = f"R{max_round_num}" if max_round_num else None

        tournaments = []
        for tournament_name, data in tournaments_data.items():
            tournaments.append(TournamentData(
                tournament_url=url_to_name.get(tournament_name, ""),
                tournament_name=tournament_name,
                max_round=data.get('max_round'),
                today_html=data.get('today_html'),
                tomorrow_html=data.get('tomorrow_html')
            ))

        return TwoDaysResponse(
            status="success",
            message=f"Successfully scraped today and tomorrow schedules for {len(tournaments)} tournaments",
            tournaments=tournaments
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=600)
