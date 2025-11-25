import os
import json
import asyncio
from schema import DrawDataRequest
from playwright.async_api import Playwright, async_playwright, Page
from script.get_match_html import create_browser_context, close_popup_if_exists

async def get_draws(playwright: Playwright, request: DrawDataRequest, target_url: str):
    """
    Get draw data for a tournament
    """

    results = {}
    draws_data= {}
    browser, context, page = await create_browser_context(playwright)
    async def log_response(response):
        if response.url == target_url:
            try:
                json_data = await response.json()
                results.update(json_data)
            except Exception as e:
                print(f"Error parsing JSON response: {e}")

    try:
        # Register response listener - Playwright automatically handles async callbacks
        page.on("response", log_response)
        print(f"Navigating to {request.tournament_url}")
        if request.tournament_url.startswith("https://bwfworldtour.bwfbadminton.com/"):
            draws_url = request.tournament_url.split("/results/")[0] + "/draws/"
            await page.goto(draws_url, wait_until="domcontentloaded", timeout=10000)
        else:
            await page.goto(request.tournament_url, wait_until="domcontentloaded", timeout=10000)
        await close_popup_if_exists(page)
        
        # Wait a bit to ensure response is captured
        await page.wait_for_timeout(2000)

        for draw in results.get('results', []):
            if draw.get('qualification'):
                continue
            draws_data[draw.get('text')] = {
                "value": draw.get('value'),
                "max_round": ""
            }
        
        return draws_data
    except Exception as e:
        print(f"Error navigating to {request.tournament_url}: {e}")
        return {}
    finally:
        await context.close()
        await browser.close()
                

async def process_all_modes(page: Page, target_url: str, draw_data: dict) -> dict[str, str]:
    """
    Process all modes from the draws page and get their max rounds
    
    Args:
        page: Playwright page object (should already be on the draws page)
    
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    
    Raises:
        InvalidTournamentFormatError: If any mode has invalid round format
    """
    matches_data = {}
    async def max_round_log_response(response):
        if response.url == target_url:
            try:
                json_data = await response.json()
                matches_data.update(json_data)

            except Exception as e:
                print(f"Error parsing JSON response: {e}")
    
    # Register response listener before processing modes
    page.on("response", max_round_log_response)
    
    # Get all modes from dropdown
    all_modes = draw_data.keys()
    print(f"Found {len(all_modes)} modes: {all_modes}")
    
    # For each mode, find its max round
    for mode in all_modes:
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

                # Extract roundName from first match in matches_data
                results = matches_data.get('results', {})
                if results:
                    # Get first match data from results dictionary
                    first_match_data = next(iter(results.values()))
                    rounds = first_match_data.get('match', {}).get('roundName', '')
                    if rounds:
                        draw_data[mode]["max_round"] = rounds
                        print(f"Mode {mode} max round: {rounds}")
                    else:
                        print(f"Could not find roundName for mode {mode}")
                else:
                    print(f"No results found in matches_data for mode {mode}")

        except Exception as e:
            print(f"Error processing mode {mode}: {e}")
            continue
    
    return draw_data


async def fetch_max_round_by_url(playwright: Playwright, url: str, target_url: str, draw_data: dict) -> dict[str, str]:
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
        await close_popup_if_exists(page)
        await page.wait_for_timeout(3000)
        
        # Process all modes
        return await process_all_modes(page, target_url, draw_data)
        
    except InvalidTournamentFormatError:
        raise
    except Exception as e:
        print(f"Error fetching mode max rounds: {e}")
        raise
    finally:
        await context.close()
        await browser.close()


async def fetch_max_round(playwright: Playwright, tmt_url: str, target_url: str, draw_data: dict) -> dict[str, str]:
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
        print(f"Navigating to tournament URL: {tmt_url}")
        await page.goto(tmt_url, wait_until="domcontentloaded", timeout=30000)
        await close_popup_if_exists(page)
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
        return await process_all_modes(page, target_url, draw_data)
        
    except InvalidTournamentFormatError:
        raise
    except Exception as e:
        print(f"Error fetching mode max rounds: {e}")
        raise
    finally:
        await context.close()
        await browser.close()



async def get_draw_max_rounds(playwright: Playwright, request: DrawDataRequest, target_url: str, draw_data: dict):
    """
    Get draw max rounds for a tournament
    """
    try:
        if request.tournament_url.startswith("https://bwfworldtour.bwfbadminton.com/"):
            max_round_data = await fetch_max_round_by_url(playwright, request.tournament_url, target_url, draw_data)
        else:
            max_round_data = await fetch_max_round(playwright, request.tournament_url, target_url, draw_data)
        
        return max_round_data
    except Exception as e:
        print(f"Error getting draw max rounds: {e}")
        return draw_data


async def main(request: DrawDataRequest):
    """
    Get draw data for a tournament
    """
    draws_target_url = "https://extranet-lv.bwfbadminton.com/api/vue-tournament-draws"
    max_rounds_target_url = "https://extranet-lv.bwfbadminton.com/api/vue-tournament-draw-data"
    # Check if cached file exists (use league_id as filename)
    draw_data_file = os.path.join("draw_data", f"{request.tournament_id}.json")
    if os.path.exists(draw_data_file):
        print(f"Loading draws data from {draw_data_file}")
        with open(draw_data_file, 'r', encoding='utf-8') as f:
            draws_data = json.load(f)
            return draws_data
    
    async with async_playwright() as playwright:
        draws_data = await get_draws(playwright, request, draws_target_url)
        if len(draws_data) == 0:
            return {}

        draws_data = await get_draw_max_rounds(playwright, request, max_rounds_target_url, draws_data)
        
        if draws_data:
            draws_data["league_name"] = request.tournament_name
            # Ensure directory exists before saving
            draw_data_dir = os.path.dirname(draw_data_file)
            os.makedirs(draw_data_dir, exist_ok=True)
            # Save to file for future use
            with open(draw_data_file, 'w', encoding='utf-8') as f:
                json.dump(draws_data, f, ensure_ascii=False, indent=4)
            return draws_data
        else:
            return {}