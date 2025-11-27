from utils.match_constants import ROUND_TO_CURRENT_ROUND_MAPPING, MODE_CODE_TO_NAME
from fastapi import HTTPException
from schema import MatchInfoRequest
import re
from utils import setup_logger
logger = setup_logger(__name__)

def get_age_category(tmt_level: str) -> str:
    """
    Get age category from tournament level
    
    Returns:
    - Age category
    """
    if "junior" in tmt_level.lower():
        return "Juniors"
    else:
        return "Adults"

def calculate_max_round(mode: str, draw_data: dict) -> str:
    """
    Calculate max round from draw data
    
    Args:
        mode: Mode string like "MS", "MS - Qualification", "WD-U19", "XD U15 - Qualification", etc.
        draw_data: Dictionary with mode as key and max_round info
    
    Returns:
    - Max round string
    """
    # Remove "- Qualification" or similar suffixes, but keep age groups (U15, U19, etc.)
    # Examples:
    #   "MS - Qualification" -> "MS"
    #   "WD-U19" -> "WD-U19"
    #   "XD U15 - Qualification" -> "XD U15"
    
    # First, try to find with original mode (in case draw_data uses exact format like "XD-U19")
    if mode in draw_data:
        return draw_data[mode].get("max_round", "")
    
    # Remove Qualification/Qualifying keywords first (before normalizing dashes)
    mode_without_qual = re.sub(r'\s*(Qualification|Qualifying|Qual)\s*', '', mode, flags=re.IGNORECASE)
    mode_without_qual = ' '.join(mode_without_qual.split())  # Trim extra spaces
    
    # Try with mode without qualification (keeping original dash format)
    if mode_without_qual in draw_data:
        return draw_data[mode_without_qual].get("max_round", "")
    
    # Normalize dashes to spaces for matching
    mode_normalized = mode_without_qual.replace("-", " ")
    mode_normalized = ' '.join(mode_normalized.split())  # Trim extra spaces
    
    # Try to find with normalized mode key (spaces instead of dashes)
    if mode_normalized in draw_data:
        return draw_data[mode_normalized].get("max_round", "")
    
    # If not found, try with just the base mode code (MS, WS, MD, WD, XD)
    mode_pattern = r'^(MS|WS|MD|WD|XD)'
    match = re.search(mode_pattern, mode_normalized)
    if match:
        base_mode = match.group(1)
        return draw_data.get(base_mode, {}).get("max_round", "")
    
    return ""


def calculate_current_round(round: str, max_round: str) -> str:
    """
    Calculate current round from round and max round
    
    Returns:
    - Current round
    """
    # Check if it's a qualifying round (e.g., "Qual. R64", "Qual. QF", "Qual. R16")
    qual_match = re.search(r'Qual[^\w]', round, re.IGNORECASE)
    if qual_match:
        return "Qualifying"
    
    # If it contains "Qualifying" or "Qualification"
    if re.search(r'Qualif\w*', round, re.IGNORECASE):
        return "Qualifying"

    current_round = ROUND_TO_CURRENT_ROUND_MAPPING.get(max_round, {}).get(round, "")
    if not current_round:
        raise ValueError(f"Current round not found for round: {round} and max round: {max_round}")

    return current_round


def extract_mode(mode: str) -> str:
    """
    Extract and convert match mode from text to full name
    
    Args:
        text: Text like "XD U15 - Qualification", "MS", "WD-U19", etc.
    
    Returns:
        Mode like "Mixed Doubles U15", "Men Singles", "Women Singles U17", etc.
    """
    mode_pattern = r'^(MS|WS|MD|WD|XD)'
    mode = mode.replace("-", " ")
    match = re.search(mode_pattern, mode.strip())
    if not match:
        return ""
    
    mode_code = match.group(1) 
    mode_name = MODE_CODE_TO_NAME.get(mode_code, mode_code)
    
    # Check for age group (U15, U17, U19, etc.)
    age_pattern = r'\bU(\d+)\b'
    age_match = re.search(age_pattern, mode)
    if age_match:
        age_group = age_match.group(0)  # e.g., "U15"
        return f"{mode_name} {age_group}"
    
    return mode_name

async def main(request: MatchInfoRequest):
    """
    Mapping match info for each match
    
    Returns:
    - MatchInfoResponse with match info
    """
    try:

        for match in request.matches_data:

            # League info
            match["league_id"] = request.tmt_id
            match["league_name"] = request.tmt_name
            match["level"] = request.tmt_level

            # Age category
            age_category = get_age_category(request.tmt_level)
            match["age_category"] = age_category

            # Max round
            max_round = calculate_max_round(match["mode"], request.draw_data)
            match["max_round"] = max_round

            # Mapping current round
            current_round = calculate_current_round(match["round"], max_round)
            match["current_round"] = current_round

            # Mapping mode code to name
            mode_name = extract_mode(match["mode"])
            match["mode"] = mode_name

        return request.matches_data

    except Exception as e:
        logger.error(f"Failed to map match info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to map match info: {str(e)}"
        )