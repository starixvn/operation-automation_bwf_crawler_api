"""
Pydantic models for Badminton Tournament Scraper API
"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional


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
    league_id: int = None
    match_id: int = None
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
    mode: str = ""
    round: str = ""
    court: str = ""
    kickoff_time: str = ""
    
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
