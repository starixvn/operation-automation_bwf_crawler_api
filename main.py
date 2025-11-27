"""
Badminton Tournament Scraper API

Provides the following endpoints:
1. GET / - API root path with endpoint information
2. GET /health - Health check endpoint
3. GET /get-tournament-list - Get current week's tournament list
4. POST /get-max-rounds - Get maximum rounds for each mode
5. POST /day-matches - Get matches for a specific tournament on a specific date
6. POST /get-draw-data - Get tournament draw data
7. POST /match-info - Map match information with tournament details
"""

from fastapi import FastAPI, HTTPException
import os
import time
from datetime import datetime

from script.get_max_rounds import get_mode_max_round_async, InvalidTournamentFormatError
from script.get_match_html import normalize_tournament_name
from script.get_matches_info_by_date import fetch_bwf_matches
from script.get_this_week_tmts import main as get_this_week_tournament_list
from script.get_draw_data import main as get_draw_data_func
from script.map_match_info import main as map_match_info_func
from script.tournament_filter import filter_tournaments
from schema import (
    MaxRoundsRequest, MaxRoundsResponse,
    DateMatchRequest, DateMatchResponse,
    ThisWeekTournamentListResponse,
    DrawDataRequest, DrawDataResponse,
    MatchInfoRequest, MatchInfoResponse,
)
from utils import clear_directory, setup_logger, cleanup_old_json_files


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
            "health": "/health",
            "get_tournament_list": "/get-tournament-list",
            "get_max_rounds": "/get-max-rounds",
            "day_matches": "/day-matches",
            "get_draw_data": "/get-draw-data",
            "match_info": "/match-info"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/get-max-rounds", response_model=MaxRoundsResponse)
async def get_max_rounds(request: MaxRoundsRequest):
    """
    Get max rounds for each mode
    
    Parameters:
    - tournament_url: Tournament URL
    - tournament_name: Tournament name
    """
    logger.info("=" * 60)
    logger.info(f"Starting getting max rounds for {request.tournament_name}")

    try:
        tournament_name = normalize_tournament_name(request.tournament_name)
        max_rounds_request = MaxRoundsRequest(tournament_name=tournament_name, tournament_url=request.tournament_url)
        mode_max_round = await get_mode_max_round_async(max_rounds_request)

        # Clean up old JSON files (older than 8 days) before processing
        cleanup_old_json_files("mode_max_round", days=8)

        return MaxRoundsResponse(
            status="success",
            message=f"Successfully got max rounds for {tournament_name}",
            tournament_url=request.tournament_url,
            tournament_name=tournament_name,
            mode_max_round=mode_max_round
        )
    except InvalidTournamentFormatError as e:
        logger.warning(f"Invalid tournament format: {str(e)}")
        logger.info("=" * 60)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tournament format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get max rounds: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get max rounds: {str(e)}"
        )


@app.post("/day-matches", response_model=DateMatchResponse)
async def scrape_specified_date_matches(request: DateMatchRequest):
    import time
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting scraping the specified date matches.")
    
    try:
        if not request.tmt_code:
            logger.warning("No league code was given.")
            raise HTTPException(status_code=400, detail="The league code is required")
        if not request.url:
            logger.warning("No league url was given.")
            raise HTTPException(status_code=400, detail="The league url is required")
        if not request.date:
            logger.warning("No date was given")
            raise HTTPException(status_code=400, detail="The specified date is required")

        # Filter tournaments
        valid_tournaments, excluded_count = filter_tournaments([request.url])
        
        if excluded_count > 0:
            logger.info(f"Excluded {excluded_count} tournament(s) based on level filters")
        
        if not valid_tournaments:
            logger.warning("No valid tournaments after filtering")
            return DateMatchResponse(
                status="success",
                message="No tournaments to scrape after filtering",
                matches=[]
            )

        tmt_code = request.tmt_code
        tmt_url = request.url
        dt = datetime.strptime(request.date, "%Y-%m-%d")
        
        logger.info(f"Fetching matches for {tmt_url} on {dt}")
        result = await fetch_bwf_matches(tmt_code, tmt_url, dt)
        match_count = len(result)
        if match_count > 0:
            res_message = f"Successfully scraped the specified date matches, total {match_count} matches."
        else:
            res_message = f"There are no matches in the specified date."
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully in {elapsed_time:.2f}s")
        logger.info("=" * 60)
        
        return DateMatchResponse(
            status = "success",
            message = res_message,
            matches = result
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@app.get("/get-tournament-list", response_model=ThisWeekTournamentListResponse)
async def get_tournament_list():
    """
    Get tournament list
    
    Returns:
    - TournamentListResponse with list of tournaments (without HTML)
    """
    try:
        tournaments = await get_this_week_tournament_list()
        return ThisWeekTournamentListResponse(
            status="success",
            message="Successfully got tournament list",
            tournaments=tournaments
        )
    except Exception as e:
        logger.error(f"Failed to get tournament list: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tournament list: {str(e)}"
        )


@app.post("/get-draw-data", response_model=DrawDataResponse)
async def get_draw_data(request: DrawDataRequest):
    """
    Get draw data
    
    Returns:
    - DrawDataResponse with draw data
    """
    try:
        start_time = time.time()
        draw_data = await get_draw_data_func(request)
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully got draw data in {elapsed_time:.2f}s")

        # Clean up old JSON files (older than 8 days) before processing
        cleanup_old_json_files("mode_max_round", days=8)
        return DrawDataResponse(
            status="success",
            message=f"Successfully got draw data in {elapsed_time:.2f}s",
            tournament_id=request.tournament_id,
            draw_data=draw_data if draw_data else {}
        )
    except Exception as e:
        logger.error(f"Failed to get draw data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get draw data: {str(e)}"
        )

@app.post("/match-info", response_model=MatchInfoResponse)
async def match_info(request: MatchInfoRequest):
    """
    Mapping match info for each match
    
    Returns:
    - MatchInfoResponse with match info
    """
    try:
        logger.info(f"Mapping match info for {request.tmt_name}")
        match_info = await map_match_info_func(request)
        return MatchInfoResponse(
            status="success",
            message="Successfully mapped match info",
            matches_data=match_info
        )
    except Exception as e:
        logger.error(f"Failed to map match info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to map match info: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=600)
