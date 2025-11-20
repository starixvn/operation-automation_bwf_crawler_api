"""
Parse match information from HTML content

This module extracts match data from BWF tournament HTML pages,
including player information, schedules, rounds, and mode details.
"""

from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Tuple
import json
import re
from datetime import datetime
import pytz
from schema import MatchData
from utils.match_constants import (
    MODE_CODE_TO_NAME,
    MODE_NAME_TO_CODE,
    VALID_MODE_CODES,
    ROUND_MAPPING,
    ROUND_TO_CURRENT_ROUND_MAPPING
)


# ==================== Date/Time Parsing ====================

def parse_time_to_iso(date_text: str, time_text: str, IANA_timezone: str, year: Optional[int] = None) -> str:
    """
    Parse date and time text to ISO format datetime string in UTC+0
    
    Args:
        date_text: Date text like "17 NOV"
        time_text: Time text like "Est. 11:30 AM" or "09:00 AM"
        IANA_timezone: IANA timezone like "Asia/Bangkok"
        year: Year to use (defaults to current year)
    
    Returns:
        ISO format datetime string in UTC+0 like "2025-11-17T04:30:00+00:00"
    """
    if year is None:
        year = datetime.now().year
    
    # Clean time text
    time_text = time_text.replace("Est.", "").replace("Followed By", "").strip()
    
    # Parse date
    try:
        date_str = f"{date_text} {year}"
        date_obj = datetime.strptime(date_str, "%d %b %Y")
    except ValueError:
        return ""
    
    # Parse time if available
    if time_text:
        try:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_text, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                meridiem = time_match.group(3).upper()
                
                # Convert to 24-hour format
                if meridiem == "PM" and hour != 12:
                    hour += 12
                elif meridiem == "AM" and hour == 12:
                    hour = 0
                
                date_obj = date_obj.replace(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            pass
    
    # Convert local time to UTC+0
    try:
        local_tz = pytz.timezone(IANA_timezone)
        local_dt = local_tz.localize(date_obj)
        utc_dt = local_dt.astimezone(pytz.UTC)
        return utc_dt.isoformat()
    except Exception:
        # If timezone conversion fails, return without timezone
        return date_obj.strftime("%Y-%m-%dT%H:%M:%S")


def extract_datetime_from_schedule(schedule_module, IANA_timezone: str) -> str:
    """
    Extract datetime from schedule module
    
    Args:
        schedule_module: BeautifulSoup element containing schedule information
        IANA_timezone: Tournament IANA timezone
    
    Returns:
        ISO format datetime string or empty string
    """
    if not schedule_module:
        return ""
    
    date_spans = schedule_module.find_all('span')
    date_text = ""
    time_text = ""
    
    for span in date_spans:
        span_text = span.get_text(strip=True)
        # Check if it's a date (like "17 NOV")
        if re.match(r'\d{1,2}\s+[A-Z]{3}', span_text):
            date_text = span_text
        # Check if it's a time (contains "AM" or "PM")
        elif 'AM' in span_text or 'PM' in span_text:
            time_text = span_text
    
    if date_text:
        return parse_time_to_iso(date_text, time_text, IANA_timezone)
    
    return ""


# ==================== Mode Extraction ====================

def extract_mode_from_text(text: str) -> str:
    """
    Extract and convert match mode from text to full name
    
    Args:
        text: Text like "XD U15 - Qualification" or "MS"
    
    Returns:
        Mode like "Mixed Doubles U15", "Men Singles", "Women Singles U17", etc.
    """
    mode_pattern = r'^(MS|WS|MD|WD|XD)'
    match = re.search(mode_pattern, text.strip())
    if not match:
        return ""
    
    mode_code = match.group(1)
    mode_name = MODE_CODE_TO_NAME.get(mode_code, mode_code)
    
    # Check for age group (U15, U17, U19, etc.)
    age_pattern = r'\bU(\d+)\b'
    age_match = re.search(age_pattern, text)
    if age_match:
        age_group = age_match.group(0)  # e.g., "U15"
        return f"{mode_name} {age_group}"
    
    return mode_name


def extract_mode_code_from_raw_text(text: str) -> str:
    """
    Extract mode code from raw HTML text, preserving age group if present
    
    Args:
        text: Raw HTML text like "MS U13 - Qualification" or "WD - Main Draw" or "MD-U19"
    
    Returns:
        Mode code like "MS U13", "MS", "WD", "MD U19", etc. (preserving age group like U13, U15, etc.)
    
    Note:
        Only processes up to the first "-" or similar separator.
        All symbols are replaced with spaces before processing.
        Handles cases like "MD-U19" where age group is after the hyphen.
    """
    # First, normalize whitespace
    text = ' '.join(text.split())
    
    # Check if there's a hyphen - if so, we need to extract mode and age group from both sides
    if '-' in text:
        # Split by "-" to get parts
        parts_before_hyphen = text.split('-')[0].strip()
        parts_after_hyphen = text.split('-', 1)[1].strip() if len(text.split('-')) > 1 else ""
        
        # Combine both parts to capture age group that might be after hyphen (e.g., "MD-U19")
        # But only take the part before any descriptive text like "Qualification" or "Main Draw"
        combined_text = parts_before_hyphen
        if parts_after_hyphen:
            # Check if the part after hyphen starts with an age group (U13, U15, etc.)
            age_group_match = re.search(r'^(U\d+)', parts_after_hyphen, re.IGNORECASE)
            if age_group_match:
                combined_text = f"{parts_before_hyphen} {age_group_match.group(1)}"
            else:
                # Otherwise, just use the part before hyphen
                combined_text = parts_before_hyphen
    else:
        combined_text = text
    
    # Replace all symbols with spaces (except alphanumeric and spaces)
    text_cleaned = re.sub(r'[^\w\s]', ' ', combined_text)
    text_cleaned = ' '.join(text_cleaned.split())
    
    parts = text_cleaned.split()
    if not parts:
        return ""
    
    mode_code = parts[0].upper()
    if mode_code not in VALID_MODE_CODES:
        return ""
    
    # Check if there's an age group (U13, U15, U17, etc.)
    age_group_pattern = r'^U\d+$'
    result_parts = [mode_code]
    
    for part in parts[1:]:
        if re.match(age_group_pattern, part.upper()):
            result_parts.append(part.upper())
            break  # Only take the first age group
    
    return ' '.join(result_parts)


def extract_mode_code(mode: str) -> str:
    """
    Extract mode code (MS, WS, MD, WD, XD) from full mode name
    
    Args:
        mode: Full mode name like "Men Singles", "Women Singles U15", etc.
    
    Returns:
        Mode code like "MS", "WS", "MD", "WD", "XD" or empty string
    """
    for full_name, code in MODE_NAME_TO_CODE.items():
        if mode.startswith(full_name):
            return code
    return ""


# ==================== Round Extraction ====================

def extract_round_from_text(text: str) -> str:
    """
    Extract round information from text, preserving original format
    
    Args:
        text: Text like "Qual. R16" or "R32" or "QF" or "Final"
    
    Returns:
        Original round text like "Qual. R64", "R32", "Quarter Final", "Final", etc.
        This preserves the original format from HTML
    """
    return text.strip()


def extract_normalized_round_for_mapping(text: str) -> str:
    """
    Extract normalized round from text for mapping purposes
    
    Args:
        text: Text like "Qual. R64" or "R32" or "QF" or "Final" or "Qual. QF"
    
    Returns:
        Normalized round like "R64", "R32", "Quarter Final", "Final", "Qualifying", etc.
        Used for mapping to current_round
    """
    # Check if it's a qualifying round (e.g., "Qual. R64", "Qual. QF", "Qual. R16")
    qual_match = re.search(r'Qual[^\w]', text, re.IGNORECASE)
    if qual_match:
        return "Qualifying"
    
    # If it contains "Qualifying" or "Qualification"
    if re.search(r'Qualif\w*', text, re.IGNORECASE):
        return "Qualifying"
    
    # Then try to match round patterns (R128, R64, R32, R16, QF, SF, Final)
    for round_code, round_name in ROUND_MAPPING.items():
        if round_code in text.upper():
            return round_name
    
    # Default: return original text capitalized
    text_cleaned = re.sub(r'[^\w\s]', ' ', text)
    text_cleaned = ' '.join(text_cleaned.split())
    words = text_cleaned.split()
    capitalized = ' '.join(word.capitalize() for word in words)
    return capitalized


def calculate_current_round(round_str: str, max_round: str) -> str:
    """
    Calculate current_round from round and max_round using ROUND_TO_CURRENT_ROUND_MAPPING
    
    Args:
        round_str: Normalized round string (e.g., "R32", "Qualifying", "Quarter Final")
        max_round: Max round for this mode (e.g., "R128", "R32")
    
    Returns:
        Current round (e.g., "R1", "R2", "Quarter Final", "Final")
    """
    if not max_round or max_round not in ROUND_TO_CURRENT_ROUND_MAPPING:
        return round_str
    
    mapping = ROUND_TO_CURRENT_ROUND_MAPPING[max_round]
    return mapping.get(round_str, round_str)


# ==================== Participant Extraction ====================

def extract_participant_info(participant_wrapper) -> Tuple[str, str, str, str, str, str]:
    """
    Extract participant information from a participant wrapper
    
    Args:
        participant_wrapper: BeautifulSoup element containing participant information
    
    Returns:
        Tuple of (player1, player1_id, player2, player2_id, country1, country2)
    """
    player1 = ""
    player1_id = ""
    player2 = ""
    player2_id = ""
    country1 = ""
    country2 = ""
    
    # Get country from flag
    flag_img = participant_wrapper.find('img', class_='flag')
    if flag_img:
        country1 = flag_img.get('alt', '')
    
    # Get player names and IDs
    player_links = participant_wrapper.find_all('a', class_='participant-name')
    
    if len(player_links) >= 1:
        player1 = player_links[0].get_text(strip=True)
        player1_id = player_links[0].get('data-player', '')
        # Get country from data-country-code if available
        country_code = player_links[0].get('data-country-code', '')
        if country_code:
            country1 = country_code
        country2 = country1  # Same country for doubles
    
    if len(player_links) >= 2:
        player2 = player_links[1].get_text(strip=True)
        player2_id = player_links[1].get('data-player', '')
        # Get country from data-country-code if available
        country_code = player_links[1].get('data-country-code', '')
        if country_code:
            country2 = country_code
    
    return player1, player1_id, player2, player2_id, country1, country2


def extract_match_info_from_card(card, IANA_timezone: str, mode_max_round: Dict[str, str], court_number: int = 0) -> Optional[MatchData]:
    """
    Extract match information from a single match card
    
    Args:
        card: BeautifulSoup element containing match card information
        IANA_timezone: Tournament IANA timezone
        mode_max_round: Max rounds for each mode (Format: {"MS": "R32", "WS": "R16", ...})
        court_number: Court number in the page order (default: 0)
    
    Returns:
        MatchData object or None if parsing fails
    """
    try:
        # Extract participants
        participant_wrappers = card.find_all('div', class_='participant-wrapper')
        
        # Home team (first participant-wrapper)
        home_player1 = ""
        home_player1_id = ""
        home_player2 = ""
        home_player2_id = ""
        home_country1 = ""
        home_country2 = ""
        
        if len(participant_wrappers) > 0:
            home_player1, home_player1_id, home_player2, home_player2_id, home_country1, home_country2 = \
                extract_participant_info(participant_wrappers[0])
        
        # Away team (second participant-wrapper)
        away_player1 = ""
        away_player1_id = ""
        away_player2 = ""
        away_player2_id = ""
        away_country1 = ""
        away_country2 = ""
        
        if len(participant_wrappers) > 1:
            away_player1, away_player1_id, away_player2, away_player2_id, away_country1, away_country2 = \
                extract_participant_info(participant_wrappers[1])
        
        # Extract schedule information
        schedule_module = card.find('div', class_='schedule-module')
        local_datetime = extract_datetime_from_schedule(schedule_module, IANA_timezone)
        
        # Extract court, mode, and round from footer
        court = ""
        mode = ""
        mode_text_raw = ""
        round_info = ""
        round_normalized = ""
        
        footer = card.find('div', class_='footer-wrapper')
        if footer:
            footer_labels = footer.find_all('span', class_='footer-label')
            
            if len(footer_labels) >= 3:
                # First label: mode information (e.g., "XD U15 - Qualification")
                mode_text_raw = footer_labels[0].get_text(strip=True)
                mode = extract_mode_from_text(mode_text_raw)
                
                # Second label: round information (e.g., "Qual. R16")
                round_text = footer_labels[1].get_text(strip=True)
                round_info = extract_round_from_text(round_text)  # Preserve original format
                round_normalized = extract_normalized_round_for_mapping(round_text)  # For mapping
                
                # Third label: court information (e.g., "Court 01")
                court = footer_labels[2].get_text(strip=True)
        
        # Calculate max_round and current_round
        max_round = ""
        current_round = round_info  # Default to original round_info if cannot calculate
        
        if mode_text_raw and mode_max_round and round_normalized:
            mode_code_full = extract_mode_code_from_raw_text(mode_text_raw)
            if mode_code_full:
                # Try to find max_round in mode_max_round
                # First try with full mode code (e.g., "MS U15")
                if mode_code_full in mode_max_round:
                    max_round = mode_max_round[mode_code_full]
                    current_round = calculate_current_round(round_normalized, max_round)
                else:
                    # Fallback to base mode code (e.g., "MS")
                    base_mode_code = mode_code_full.split()[0]
                    if base_mode_code in mode_max_round:
                        max_round = mode_max_round[base_mode_code]
                        current_round = calculate_current_round(round_normalized, max_round)
        
        # Create MatchData object (match_number and match_id will be assigned later)
        return MatchData(
            match_id=0,  # Temporary value, will be calculated below
            local_datetime=local_datetime,
            IANA_timezone=IANA_timezone,
            home_player1=home_player1,
            home_player1_id=home_player1_id,
            home_player2=home_player2,
            home_player2_id=home_player2_id,
            home_country1=home_country1,
            home_country2=home_country2,
            away_player1=away_player1,
            away_player1_id=away_player1_id,
            away_player2=away_player2,
            away_player2_id=away_player2_id,
            away_country1=away_country1,
            away_country2=away_country2,
            court=court,
            court_number=court_number,
            round=round_info,
            current_round=current_round,
            max_round=max_round,
            mode=mode,
            match_number=0  # Temporary value, will be calculated below
        )
    
    except Exception as e:
        print(f"Error parsing match card: {str(e)}")
        return None


def assign_match_numbers(matches: List[MatchData]) -> None:
    """
    Assign match numbers by court
    
    Args:
        matches: List of MatchData objects to assign numbers to
    """
    court_counters: Dict[str, int] = {}
    
    for match in matches:
        court_name = match.court
        
        if court_name not in court_counters:
            court_counters[court_name] = 0
        
        court_counters[court_name] += 1
        match.match_number = court_counters[court_name]


def generate_match_id(league_id: str, local_datetime: str, court_number: int, match_number: int) -> int:
    """
    Generate match_id from league_id + local_date + court_number + match_number
    
    Format: league_id + YYYYMMDD + court_number(2 digits) + match_number(2 digits)
    Example: 5557202511180203
    
    Args:
        league_id: League ID string
        local_datetime: ISO format datetime string (e.g., "2025-11-18T04:30:00+00:00")
        court_number: Court number
        match_number: Match number
    
    Returns:
        Match ID as integer
    """
    if not league_id or not local_datetime:
        return 0
    
    # Extract date from ISO format datetime (YYYY-MM-DD)
    try:
        date_part = local_datetime.split('T')[0]  # Get YYYY-MM-DD
        date_str = date_part.replace('-', '')  # Convert to YYYYMMDD
    except (IndexError, AttributeError):
        return 0
    
    # Format court_number and match_number as 2-digit strings
    court_str = f"{court_number:02d}"
    match_str = f"{match_number:02d}"
    
    # Combine: league_id + date + court_number + match_number
    match_id_str = f"{league_id}{date_str}{court_str}{match_str}"
    
    try:
        return int(match_id_str)
    except ValueError:
        return 0


def assign_match_ids(matches: List[MatchData], league_id: str) -> None:
    """
    Assign match IDs to matches
    
    Args:
        matches: List of MatchData objects to assign IDs to
        league_id: League ID for generating match_id
    """
    for match in matches:
        match.match_id = generate_match_id(
            league_id,
            match.local_datetime,
            match.court_number,
            match.match_number
        )


# ==================== Main Function ====================

def get_matches_info(html: str, IANA_timezone: str, mode_max_round: Optional[Dict[str, str]] = None, league_id: str = "") -> List[MatchData]:
    """
    Main function to get matches info from HTML content

    Args:
        html: HTML content of the matches page
        IANA_timezone: Tournament IANA timezone
        mode_max_round: Max rounds for each mode (Format: {"MS": "R32", "WS": "R16", ...})
        league_id: League ID for generating match_id (default: "")
    
    Returns:
        List of MatchData objects
    """
    if mode_max_round is None:
        mode_max_round = {}
    
    soup = BeautifulSoup(html, 'html.parser')
    match_cards = soup.find_all('div', class_='match-card')
    
    # Track court order in the page (including empty courts)
    court_order: Dict[str, int] = {}
    court_counter = 0
    empty_block_counter = 0  # Counter for empty court blocks
    prev_court_key = None  # Track previous match's court key
    current_empty_block_key = None  # Track current empty block key
    
    matches = []
    for card in match_cards:
        # Extract court first to determine court_number
        court = ""
        footer = card.find('div', class_='footer-wrapper')
        if footer:
            footer_labels = footer.find_all('span', class_='footer-label')
            if len(footer_labels) >= 3:
                court = footer_labels[2].get_text(strip=True)
        
        # Determine court_key and court_number
        if court:
            # Has court: use court name as key
            court_key = court
            if court_key not in court_order:
                court_counter += 1
                court_order[court_key] = court_counter
            court_number = court_order[court_key]
            current_empty_block_key = None  # Reset empty block key when we have a court
        else:
            # No court: check if this is a continuation of an empty block
            if prev_court_key is None or prev_court_key != "":
                # Start of a new empty block
                empty_block_counter += 1
                current_empty_block_key = f"EMPTY_{empty_block_counter}"
                court_counter += 1
                court_order[current_empty_block_key] = court_counter
            # Use the current empty block's court_number
            court_number = court_order[current_empty_block_key]
            court_key = ""
        
        prev_court_key = court_key
        
        match_data = extract_match_info_from_card(card, IANA_timezone, mode_max_round, court_number)
        if match_data:
            matches.append(match_data)
    
    # Assign match numbers by court
    assign_match_numbers(matches)
    
    # Assign match IDs
    if league_id:
        assign_match_ids(matches, league_id)
    
    return matches


# ==================== Test/CLI ====================

if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    request_file = "test_html.json"
    with open(request_file, 'r') as f:
        request_data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(request_data, list) and len(request_data) > 0:
        request = request_data[0]
    elif isinstance(request_data, dict):
        request = request_data
    else:
        print("錯誤：test_html.json 格式不正確")
        sys.exit(1)
    
    matches = get_matches_info(
        request['html'], 
        request.get('IANA_timezone', ''),
        request.get('mode_max_round', {}),
        request.get('league_id', '')
    )
    
    print(f"\n總共解析了 {len(matches)} 場比賽：\n")
    
    # Print first 3 matches as examples
    for i, match in enumerate(matches[:3]):
        print(f"比賽 {i+1}:")
        print(f"  Match ID: {match.match_id}")
        print(f"  Match Number: {match.match_number}")
        print(f"  時間: {match.local_datetime}")
        print(f"  時區: {match.IANA_timezone}")
        print(f"  主場: {match.home_player1} {match.home_player2}".strip())
        print(f"  主場國家: {match.home_country1} {match.home_country2}".strip())
        print(f"  客場: {match.away_player1} {match.away_player2}".strip())
        print(f"  客場國家: {match.away_country1} {match.away_country2}".strip())
        print(f"  球場: {match.court}")
        print(f"  球場編號: {match.court_number}")
        print(f"  輪次: {match.round}")
        print(f"  當前輪次: {match.current_round}")
        print(f"  最大輪次: {match.max_round}")
        print(f"  模式: {match.mode}")
        print()
    
    if len(matches) > 3:
        print(f"... 還有 {len(matches) - 3} 場比賽\n")
    
    # Convert matches to JSON format
    matches_json = []
    for match in matches:
        matches_json.append({
            "match_id": match.match_id,
            "local_datetime": match.local_datetime,
            "IANA_timezone": match.IANA_timezone,
            "home_player1": match.home_player1,
            "home_player1_id": match.home_player1_id,
            "home_player2": match.home_player2,
            "home_player2_id": match.home_player2_id,
            "home_country1": match.home_country1,
            "home_country2": match.home_country2,
            "away_player1": match.away_player1,
            "away_player1_id": match.away_player1_id,
            "away_player2": match.away_player2,
            "away_player2_id": match.away_player2_id,
            "away_country1": match.away_country1,
            "away_country2": match.away_country2,
            "court": match.court,
            "court_number": match.court_number,
            "round": match.round,
            "current_round": match.current_round,
            "max_round": match.max_round,
            "mode": match.mode,
            "match_number": match.match_number
        })
    
    # Save to JSON file
    output_data = {
        "tournament_name": request.get('league_name', ''),
        "level": request.get('level', ''),
        "country": request.get('country', ''),
        "city": request.get('city', ''),
        "IANA_timezone": request.get('IANA_timezone', ''),
        "parsed_at": datetime.now().isoformat(),
        "total_matches": len(matches),
        "matches": matches_json
    }
    
    output_file = "parsed_matches.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功保存 {len(matches)} 場比賽到 {output_file}")
