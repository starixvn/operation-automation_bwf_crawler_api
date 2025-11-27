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
    # mode_max_round: Optional[dict] = None  # Format: {"MS": "R32", "WS": "R16", ...}
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


class ParseMatchesRequest(BaseModel):
    """Parse matches HTML request model"""
    html: str
    tournament_name: str
    level: str
    country: str = ""
    city: str = ""
    IANA_timezone: str = ""
    mode_max_round: dict[str, str]  # Format: {"MS": "R32", "WS": "R16", ...}
    league_id: str = ""  # League ID for generating match_id


class MatchData(BaseModel):
    """Single match data"""
    match_id: int
    local_datetime: str  # ISO format in UTC+0: YYYY-MM-DDTHH:MM:SS+00:00 (converted from local time)
    IANA_timezone: str  # Original timezone of the tournament
    home_player1: str
    home_player1_id:str
    home_player2: str
    home_player2_id:str
    home_country1: str
    home_country2: str
    away_player1: str
    away_player1_id:str
    away_player2: str
    away_player2_id:str
    away_country1: str
    away_country2: str
    court: str
    court_number: int
    round: str  # e.g., "R32", "Quarter Final", "Final"
    current_round: str  # e.g., "R1", "R2", "Quarter Final", "Final"
    max_round: str  # e.g., "R32", "R16"
    mode: str  # e.g., "Men Singles", "Women Singles", "Mixed Doubles"
    match_number: int


class ParseMatchesResponse(BaseModel):
    """Parse matches HTML response model"""
    status: str
    message: str
    matches: List[MatchData]


class MaxRoundsRequest(BaseModel):
    """Get max rounds for each mode request model"""
    tournament_url: str
    tournament_name: str

class MaxRoundsResponse(BaseModel):
    """Get max rounds for each mode response model"""
    status: str
    message: str
    tournament_url: str
    tournament_name: str
    mode_max_round: dict[str, str]  # Format: {"MS": "R32", "WS": "R16", ...}

class DateMatchData(BaseModel):
    league_id: int
    match_id: int
    player_home_1_id: Optional[int] = None
    player_home_1_country: Optional[str] = ""
    player_home_1_name: Optional[str] = ""
    player_home_2_id: Optional[int] = None
    player_home_2_country: Optional[str] = ""
    player_home_2_name: Optional[str] = ""
    player_away_1_id: Optional[int] = None
    player_away_1_country: Optional[str] = ""
    player_away_1_name: Optional[str] = ""
    player_away_2_id: Optional[int] = None
    player_away_2_country: Optional[str] = ""
    player_away_2_name: Optional[str] = ""
    mode: str
    round: str
    court: str
    kickoff_time: str
    
class DateMatchResponse(BaseModel):
    status: str
    message: str
    matches: Optional[List[DateMatchData]]

class DateMatchRequest(BaseModel):
    """Match request model with specific date"""
    tmt_code: str
    url: str
    date: str  # Format: YYYY-MM-DD

class ThisWeekTournamentListItem(BaseModel):
    """This week tournament list item"""
    tmt_id: int
    tmt_code: str
    tmt_url: str
    tmt_name: str
    tmt_level: str

class ThisWeekTournamentListResponse(BaseModel):
    """This week tournament list response model"""
    status: str
    message: str
    tournaments: List[ThisWeekTournamentListItem]

class DrawDataRequest(BaseModel):
    """Draw data request model"""
    tournament_id: str
    tournament_url: str
    tournament_name: str

class DrawDataResponse(BaseModel):
    """Draw data response model"""
    status: str
    message: str
    tournament_id: str
    draw_data: dict

class MatchInfo(DateMatchData):
    """Match info"""
    league_name: str
    level: str
    current_round: str  # e.g., "R1", "R2", "Quarter Final", "Final"
    max_round: str  # e.g., "R32", "R16"

class MatchInfoRequest(BaseModel):
    """Map max rounds request model"""
    tmt_id: int
    tmt_name: str
    tmt_level: str
    draw_data: dict
    matches_data: list

class MatchInfoResponse(BaseModel):
    """Map max rounds response model"""
    status: str
    message: str
    matches_data: list[MatchInfo]

class UpdateMatchesRequest(BaseModel):
    """Match request model with specific date and update frequency"""
    tmt_code: str
    url: str
    date: str
    update_feq: int
