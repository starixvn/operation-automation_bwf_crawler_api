"""
Pydantic models for Badminton Tournament Scraper API
"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class TournamentInput(BaseModel):
    """Single tournament input with URL and level"""
    tournament_name: str
    url: HttpUrl
    level: str = ""  # Tournament level/category
    country: str = ""  # Tournament country
    city: str = ""  # Tournament city
    IANA_timezone: str = ""  # Tournament IANA timezone


class TournamentRequest(BaseModel):
    """Tournament request model"""
    tournaments: List[TournamentInput]
    output_dir: Optional[str] = "two_days"


class DateTournamentRequest(BaseModel):
    """Tournament request model with specific date"""
    date: str  # Format: YYYY-MM-DD
    tournaments: List[TournamentInput]
    output_dir: Optional[str] = "yesterday/leagues"


class TournamentData(BaseModel):
    """Single tournament data"""
    tournament_url: str
    league_id: str
    league_name: str
    level: str
    country: str
    city: str
    IANA_timezone: str
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


class TournamentListItem(BaseModel):
    """Tournament list item (without HTML)"""
    tournament_url: str
    level: str
    country: str = ""
    city: str = ""
    IANA_timezone: str = ""


class TournamentListResponse(BaseModel):
    """Tournament list response model"""
    status: str
    message: str
    date: str
    tournaments: List[TournamentListItem]

