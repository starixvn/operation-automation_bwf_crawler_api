"""
Load match-related constants from JSON file

This module provides functions to load constants used for parsing match information,
including mode mappings and round mappings.
"""

import json
import os
from typing import Dict, Set
from functools import lru_cache


# Path to the constants JSON file
_CONSTANTS_FILE = os.path.join(os.path.dirname(__file__), "match_constants.json")


@lru_cache(maxsize=1)
def _load_constants() -> Dict:
    """
    Load constants from JSON file (cached)
    
    Returns:
        Dictionary containing all constants
    """
    with open(_CONSTANTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_mode_code_to_name() -> Dict[str, str]:
    """
    Get mode code to name mapping
    
    Returns:
        Dictionary mapping mode codes (MS, WS, etc.) to full names
    """
    return _load_constants()["MODE_CODE_TO_NAME"]


def get_mode_name_to_code() -> Dict[str, str]:
    """
    Get mode name to code mapping
    
    Returns:
        Dictionary mapping full mode names to codes
    """
    return _load_constants()["MODE_NAME_TO_CODE"]


def get_valid_mode_codes() -> Set[str]:
    """
    Get set of valid mode codes
    
    Returns:
        Set of valid mode codes (MS, WS, MD, WD, XD)
    """
    return set(_load_constants()["VALID_MODE_CODES"])


def get_round_mapping() -> Dict[str, str]:
    """
    Get round code to name mapping
    
    Returns:
        Dictionary mapping round codes (QF, SF, etc.) to full names
    """
    return _load_constants()["ROUND_MAPPING"]


def get_round_to_current_round_mapping() -> Dict[str, Dict[str, str]]:
    """
    Get round to current round mapping based on max_round
    
    Returns:
        Nested dictionary: {max_round: {round: current_round}}
    """
    return _load_constants()["ROUND_TO_CURRENT_ROUND_MAPPING"]


# Convenience variables for backward compatibility
# These are loaded once when module is imported
_constants = _load_constants()

MODE_CODE_TO_NAME = _constants["MODE_CODE_TO_NAME"]
MODE_NAME_TO_CODE = _constants["MODE_NAME_TO_CODE"]
VALID_MODE_CODES = set(_constants["VALID_MODE_CODES"])
ROUND_MAPPING = _constants["ROUND_MAPPING"]
ROUND_TO_CURRENT_ROUND_MAPPING = _constants["ROUND_TO_CURRENT_ROUND_MAPPING"]

