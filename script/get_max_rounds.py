import os
import json
import re
import asyncio
from schema import MaxRoundsRequest
from playwright.async_api import Playwright, Page, async_playwright
from script.get_match_html import create_browser_context, extract_league_id, normalize_tournament_name


class InvalidTournamentFormatError(Exception):
    """Raised when tournament round format is not in the expected standard format"""
    pass

async def get_all_modes(page: Page) -> list[str]:
    """
    Get all modes from the draws page dropdown menu
    
    Args:
        page: Playwright page object
    
    Returns:
        List of mode names (e.g., ["MS", "WS", "MD", "WD", "XD", "MS - Qualification", ...])
    """
    modes = []
    
    # Click on the dropdown to open it
    try:
        # Find the dropdown button/trigger
        dropdown_trigger = page.locator("i.fa.fas.fa-chevron-down").first
        if await dropdown_trigger.count() > 0:
            await dropdown_trigger.click()
            await page.wait_for_timeout(500)  # Wait for dropdown to open
    except Exception as e:
        print(f"Could not click dropdown trigger: {e}")
    
    # Get all mode options from group-main
    main_modes = await page.locator("div.draw-select-option.group-main").all_text_contents()
    
    # Clean up mode names
    for mode in main_modes:
        mode = mode.strip()
        # Replace all symbols (non-alphanumeric and non-space) with spaces
        mode = re.sub(r'[^\w\s]', ' ', mode)
        # Replace multiple spaces with single space
        mode = re.sub(r'\s+', ' ', mode)
        mode = mode.strip()
        if mode:
            modes.append(mode)
    
    return modes


def is_valid_round_format(round_str: str) -> bool:
    """
    Check if the round string is in valid standard format
    
    Valid formats: R32, R16, R8, R4, R2, QF, SF, F
    (R followed by a number, or QF, SF, F)
    
    Args:
        round_str: Round string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not round_str:
        return False
    
    # Check for standard formats: R##, QF, SF, F
    valid_pattern = re.compile(r'^(R\d+|QF|SF|F)$', re.IGNORECASE)
    return bool(valid_pattern.match(round_str.strip()))


async def find_mode_max_round(page: Page, mode: str) -> str:
    """
    Find the maximum round for a specific mode from the draws page
    
    Gets the first div.round-col-header element after selecting the mode,
    which contains the maximum round information (e.g., "Round 32")
    
    Args:
        page: Playwright page object
        mode: Mode name (e.g., "MS", "WS - Qualification")
    
    Returns:
        Maximum round string (e.g., "R32", "R16", "R8", "QF", "SF", "F")
    
    Raises:
        InvalidTournamentFormatError: If the round format is not in standard format
    """
    try:
        # Click on the dropdown to open it
        dropdown_trigger = page.locator("i.fa.fas.fa-chevron-down").first
        if await dropdown_trigger.count() > 0:
            await dropdown_trigger.click()
            await page.wait_for_timeout(500)
        
        # Find and click the mode option
        mode_option = page.locator(f"div.draw-select-option:has-text('{mode}')").first
        if await mode_option.count() > 0:
            await mode_option.click()
            await page.wait_for_timeout(2000)  # Wait for draws to load
        
        # Find the first div.round-col-header element
        round_header = page.locator("div.round-col-header").first
        if await round_header.count() > 0:
            round_text = await round_header.inner_text()
            round_text = round_text.strip()
            
            # Convert round text to standard format
            # Examples: "Round 32" -> "R32", "Round 16" -> "R16", "Quarter Final" -> "QF", etc.
            round_text_lower = round_text.lower()
            max_round = None
            
            # IMPORTANT: Check in order from most specific to least specific
            # Check for Quarter Final first (before Final, since "Quarter Final" contains "Final")
            if re.search(r'quarter\s+final|\bqf\b', round_text_lower):
                max_round = "QF"
            
            # Check for Semi Final (before Final, since "Semi Final" contains "Final")
            elif re.search(r'semi\s+final|\bsf\b', round_text_lower):
                max_round = "SF"
            
            # Check for Final (must be last, as it's the most general)
            # Use word boundary to avoid matching "Quarter Final" or "Semi Final"
            elif re.search(r'\bfinal\b', round_text_lower) and not re.search(r'quarter|semi', round_text_lower):
                max_round = "F"
            
            # Check for Round ## pattern (e.g., "Round 32", "Round 16")
            elif round_match := re.search(r'round\s+(\d+)', round_text_lower):
                round_num = round_match.group(1)
                max_round = f"R{round_num}"
            
            # Check for R## pattern (e.g., "R32", "R16")
            elif r_match := re.search(r'\bR(\d+)\b', round_text, re.IGNORECASE):
                round_num = r_match.group(1)
                max_round = f"R{round_num}"
            
            # If we found a valid round format, return it
            if max_round and is_valid_round_format(max_round):
                return max_round
            
            # If no valid pattern matches, raise exception
            raise InvalidTournamentFormatError(
                f"Tournament round format '{round_text}' for mode '{mode}' is not in standard format. "
                f"Expected formats: R32, R16, R8, R4, R2, QF, SF, F"
            )
        
        # If round header not found, raise exception
        raise InvalidTournamentFormatError(
            f"Could not find round header for mode '{mode}'. This tournament may not be in the expected format."
        )
        
    except InvalidTournamentFormatError:
        # Re-raise InvalidTournamentFormatError as-is
        raise
    except Exception as e:
        # Wrap other exceptions
        raise InvalidTournamentFormatError(
            f"Error finding max round for mode '{mode}': {str(e)}"
        ) from e


async def process_all_modes(page: Page) -> dict[str, str]:
    """
    Process all modes from the draws page and get their max rounds
    
    Args:
        page: Playwright page object (should already be on the draws page)
    
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    
    Raises:
        InvalidTournamentFormatError: If any mode has invalid round format
    """
    mode_max_round = {}
    
    # Get all modes from dropdown
    all_modes = await get_all_modes(page)
    print(f"Found {len(all_modes)} modes: {all_modes}")
    
    # For each mode, find its max round
    for mode in all_modes:
        print(f"Processing mode: {mode}")
        try:
            max_round = await find_mode_max_round(page, mode)
            # Validate the round format before adding
            if not is_valid_round_format(max_round):
                raise InvalidTournamentFormatError(
                    f"Mode '{mode}' has invalid round format: '{max_round}'. "
                    f"Expected formats: R32, R16, R8, R4, R2, QF, SF, F"
                )
            mode_max_round[mode] = max_round
            print(f"Mode {mode} max round: {max_round}")
        except InvalidTournamentFormatError as e:
            print(f"Invalid tournament format detected: {e}")
            print("Stopping processing - this tournament is not in the expected format.")
            raise
    
    return mode_max_round


async def fetch_mode_max_round_by_url(playwright: Playwright, url: str) -> dict[str, str]:
    """
    Fetch mode max round by converting URL to draws URL
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
    
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    browser, context, page = await create_browser_context(playwright)
    
    try:
        # Convert results URL to draws URL
        if "/results/" in url:
            draws_url = url.split("/results/")[0] + "/draws/"
        elif url.endswith("/"):
            draws_url = url.rstrip("/") + "/draws/"
        else:
            draws_url = url + "/draws/"
        
        print(f"Navigating to draws URL: {draws_url}")
        await page.goto(draws_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Process all modes
        return await process_all_modes(page)
        
    except InvalidTournamentFormatError:
        raise
    except Exception as e:
        print(f"Error fetching mode max rounds: {e}")
        raise
    finally:
        await context.close()
        await browser.close()


async def fetch_mode_max_round(playwright: Playwright, url: str) -> dict[str, str]:
    """
    Fetch mode max round by clicking DRAWS tab
    
    Navigates to the tournament URL, clicks on the DRAWS tab,
    then processes all modes to get their max rounds.
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
    
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    browser, context, page = await create_browser_context(playwright)
    
    try:
        print(f"Navigating to tournament URL: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Find and click the DRAWS tab
        draws_tab = page.locator("ul.cal-event-tabs.tournament-tabs li:has-text('DRAWS') a")
        if await draws_tab.count() > 0:
            await draws_tab.click()
            await page.wait_for_timeout(2000)  # Wait for draws tab to load
            print("Clicked on DRAWS tab")
        else:
            raise Exception("Could not find DRAWS tab on the tournament page")
        
        # Process all modes
        return await process_all_modes(page)
        
    except InvalidTournamentFormatError:
        raise
    except Exception as e:
        print(f"Error fetching mode max rounds: {e}")
        raise
    finally:
        await context.close()
        await browser.close()


async def get_mode_max_round_async(request: MaxRoundsRequest) -> dict[str, str]:
    """
    Get max rounds for each mode (async version)
    
    Args:
        request: MaxRoundsRequest object

    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    # Create mode_max_round directory if it doesn't exist
    os.makedirs("mode_max_round", exist_ok=True)
    
    # Extract league_id from tournament URL
    league_id = extract_league_id(request.tournament_url)
    if not league_id:
        raise ValueError(f"Could not extract league_id from URL: {request.tournament_url}")
    
    # Check if cached file exists (use league_id as filename)
    mode_max_round_file = os.path.join("mode_max_round", f"{league_id}.json")
    if os.path.exists(mode_max_round_file):
        with open(mode_max_round_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fetch from website based on URL type
    async with async_playwright() as playwright:
        if request.tournament_url.startswith("https://bwfworldtour.bwfbadminton.com/"):
            mode_max_round = await fetch_mode_max_round_by_url(playwright, request.tournament_url)
        else:
            mode_max_round = await fetch_mode_max_round(playwright, request.tournament_url)
    
    # Save to file for future use (use league_id as filename)
    with open(mode_max_round_file, 'w', encoding='utf-8') as f:
        tournament_name = normalize_tournament_name(request.tournament_name)
        mode_max_round["league_name"] = tournament_name
        json.dump(mode_max_round, f, ensure_ascii=False, indent=2)
    
    return mode_max_round


def get_mode_max_round(request: MaxRoundsRequest) -> dict[str, str]:
    """
    Get max rounds for each mode (synchronous wrapper)
    
    Args:
        request: MaxRoundsRequest object

    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    return asyncio.run(get_mode_max_round_async(request))


if __name__ == "__main__":
    # request = MaxRoundsRequest(
    #     tournament_name="Australian Open",
    #     tournament_url="https://bwfworldtour.bwfbadminton.com/tournament/5199/sathio-group-australian-open-2025/results/",
    # )
    request = MaxRoundsRequest(
        tournament_name="Pathum thani junior international series",
        tournament_url="https://bwfbadminton.com/tournament/5507/bat-yonex-pathum-thani-junior-international-series-2025/results/"
    )
    mode_max_round = get_mode_max_round(request)
    print(mode_max_round)