"""
Tournament filtering logic
"""

from typing import List


# Excluded tournament levels
EXCLUDED_LEVELS = {
    "International Series",
    "International Challenge",
    "Junior International Series",
    "Junior Tournament"
}


def should_exclude_tournament(tmt_url: str) -> bool:
    """
    Check if a tournament should be excluded based on its level
    
    Exclusion rules:
    1. Empty level
    2. Level contains "para" (case insensitive)
    3. Level matches excluded levels (case insensitive)
    
    Args:
        tournament: TournamentInput object
        
    Returns:
        True if tournament should be excluded, False otherwise
    """
    # Skip if level is empty
    # if not tournament.level or not tournament.level.strip():
    #     return True
    
    # Skip if level contains "para" (case insensitive)
    if "para" in tmt_url.lower():
        return True
    
    # Skip if level is in excluded list (case insensitive comparison)
    # if any(tournament.level.lower() == excluded.lower() for excluded in EXCLUDED_LEVELS):
    #     return True
    
    return False


def filter_tournaments(tmt_url: List[str]) -> tuple[List[str], int]:
    """
    Filter out excluded tournaments
    
    Args:
        tournaments: List of TournamentInput objects
        
    Returns:
        Tuple of (valid_tournaments, excluded_count)
    """
    valid_tournaments = [t for t in tmt_url if not should_exclude_tournament(t)]
    excluded_count = len(tmt_url) - len(valid_tournaments)

    return valid_tournaments, excluded_count

