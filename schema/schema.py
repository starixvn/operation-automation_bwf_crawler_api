"""
Pydantic models for Badminton Tournament Scraper API
"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class TournamentInput(BaseModel):
    """Single tournament input with URL and level"""
    url: HttpUrl
    level: str = ""  # Tournament level/category


class TournamentRequest(BaseModel):
    """Tournament request model"""
    tournaments: List[TournamentInput]
    output_dir: Optional[str] = "two_days"


class TournamentData(BaseModel):
    """Single tournament data"""
    tournament_url: str
    league_id: str
    league_name: str
    level: str
    age_category: str  # "Juniors" or "Adults"
    mode_max_round: Optional[dict] = None  # Format: {"MS": "R32", "WS": "R16", ...}
    today_html: Optional[str] = None  # HTML content as string
    tomorrow_html: Optional[str] = None  # HTML content as string


class ScrapeResponse(BaseModel):
    """Scraper response model"""
    status: str  # success, failed
    message: str
    timestamp: str
    output_dir: Optional[str] = None
    files: Optional[dict] = None  # Filename to HTML content (string) mapping


class TwoDaysResponse(BaseModel):
    """Two-days schedule response model"""
    status: str
    message: str
    tournaments: List[TournamentData]

