"""
Common functions for scraping badminton tournament matches
Shared utilities for all match scraping scripts
"""

import re
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from unidecode import unidecode
from playwright.async_api import Page, Playwright


# ==================== URL & Name Processing ====================

def extract_tournament_name(url: str) -> str:
    """
    Extract tournament name from URL
    
    Args:
        url: tournament URL
        
    Returns:
        Tournament name
    """
    url = re.sub(r'/\d{4}-\d{2}-\d{2}/?$', '', url)
    url = re.sub(r'/results/?$', '', url)
    url = url.rstrip('/')
    tournament_name = url.split("/")[-1]
    return tournament_name


def extract_league_id(url: str) -> str:
    """
    Extract league ID from tournament URL
    
    Args:
        url: Tournament URL
        
    Returns:
        League ID (numeric)
    """
    if not url:
        return ""
    
    match = re.search(r'/tournament/(\d+)/', url)
    if match:
        return match.group(1)
    
    return ""


def format_tournament_name(raw_name: str) -> str:
    """
    Format tournament name by replacing dashes with spaces and capitalizing
    
    Args:
        raw_name: Raw tournament name with dashes
        
    Returns:
        Formatted tournament name
    """
    if not raw_name:
        return raw_name
    
    parts = raw_name.split('-')
    formatted = ' '.join(word.capitalize() for word in parts)
    
    return formatted


def is_bwfworldtour_url(url: str) -> bool:
    """Check if URL is bwfworldtour website"""
    return "bwfworldtour" in url


def get_date_url(base_url: str, date: datetime) -> str:
    """
    Generate URL with date for bwfworldtour website
    
    Args:
        base_url: Base URL (e.g., .../results/)
        date: date object
        
    Returns:
        URL with date (e.g., .../results/2025-10-08)
    """
    base_url = base_url.rstrip('/')
    date_str = date.strftime("%Y-%m-%d")
    return f"{base_url}/{date_str}"


# ==================== HTML Processing ====================

def find_mode_max_round(html: str) -> dict[str, str]:
    """
    Find the maximum round for each mode (MS/WS/MD/WD/XD) from HTML
    
    Args:
        html: HTML content of the schedule
    
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    valid_modes = {'MS', 'WS', 'MD', 'WD', 'XD'}
    mode_max_round = {}
    
    footer_pattern = r'<div class="footer-wrapper">(.*?)</div>\s*</div>\s*</div>\s*</div>'
    footers = re.findall(footer_pattern, html, re.DOTALL)
    
    for footer in footers:
        labels = re.findall(r'<span class="footer-label">\s*([^<]+?)\s*</span>', footer)
        
        if len(labels) < 2:
            continue
            
        mode_raw = labels[0].strip()
        round_label = labels[1].strip()
        
        # Extract base mode (e.g., "MS-U19" -> "MS", "WS" -> "WS")
        mode = mode_raw.split('-')[0] if '-' in mode_raw else mode_raw
        
        if mode not in valid_modes:
            continue
            
        round_match = re.match(r'^R(\d+)$', round_label)
        if not round_match:
            continue
            
        round_num = int(round_match.group(1))
        
        if mode not in mode_max_round:
            mode_max_round[mode] = round_num
        else:
            mode_max_round[mode] = max(mode_max_round[mode], round_num)
    
    result = {mode: f"R{num}" for mode, num in mode_max_round.items()}
    
    return result


# ==================== Page Operations ====================

async def close_popup_if_exists(page: Page) -> None:
    """Close popup window if exists"""
    try:
        await page.get_by_role("button", name="Close").click()
    except Exception:
        pass


async def switch_to_list_view(page: Page) -> None:
    """Switch to List View"""
    try:
        await page.locator("label").filter(has_text="List View").locator("span").click(force=True, timeout=5000)
        await page.wait_for_timeout(1000)
    except Exception:
        pass


async def initialize_page(page: Page) -> None:
    """Initialize page: close popup, wait, switch to List View"""
    await close_popup_if_exists(page)
    await page.wait_for_timeout(2000)
    await switch_to_list_view(page)


async def get_schedule_html(page: Page) -> Optional[str]:
    """Get schedule HTML from current page"""
    if await page.get_by_role("heading", name="No schedule announced").count() > 0:
        return None

    if await page.locator(".container.results-wrapper").count() == 0:
        return None

    try:
        await page.wait_for_selector(".container.results-wrapper", timeout=3000)
        await page.wait_for_timeout(500)
    except Exception:
        return None

    return await page.locator(".container.results-wrapper").evaluate("el => el.outerHTML")


async def get_date_tabs(page: Page) -> tuple[int, any, bool]:
    """
    Get all date tabs, exclude PODIUM tab
    
    Returns:
        tuple[int, Locator, bool]: (date tab count, tab button locator, whether li format)
    """
    date_tab_container = page.locator(".container-fullwidth > .page-tab-wrapper-outer").nth(1)
    all_date_buttons = date_tab_container.locator("button, a, div[class*='tab']")
    total_tabs = await all_date_buttons.count()
    is_li_format = False

    if total_tabs == 0:
        all_date_buttons = page.locator("ul#ajaxTabsResults.days-tabs > li")
        total_tabs = await all_date_buttons.count()
        is_li_format = True

    if total_tabs == 0:
        return 0, all_date_buttons, is_li_format

    last_tab_text = await all_date_buttons.nth(total_tabs - 1).inner_text()
    if "PODIUM" in last_tab_text.upper():
        total_dates = total_tabs - 1
    else:
        total_dates = total_tabs

    return total_dates, all_date_buttons, is_li_format


# ==================== Date Handling ====================

def format_date_string(date: datetime) -> tuple[str, str, str, str]:
    """
    Format date to multiple formats
    
    Returns:
        tuple: (uppercase with zero, uppercase without zero, title case with zero, title case without zero)
    """
    upper_with_zero = date.strftime("%d %b").upper()
    upper_without_zero = date.strftime("%-d %b" if date.day < 10 else "%d %b").upper()
    title_with_zero = date.strftime("%d %b")
    title_without_zero = date.strftime("%-d %b" if date.day < 10 else "%d %b")

    return upper_with_zero, upper_without_zero, title_with_zero, title_without_zero


def find_date_tab_index(date_tab_texts: list[str], target_date: datetime) -> Optional[int]:
    """Find index of specified date in tab text list"""
    upper_with_zero, upper_without_zero, title_with_zero, title_without_zero = format_date_string(target_date)

    for i, tab_text in enumerate(date_tab_texts):
        if (upper_with_zero in tab_text or
            upper_without_zero in tab_text or
            title_with_zero in tab_text or
            title_without_zero in tab_text):
            return i

    return None


# ==================== Browser Operations ====================

async def create_browser_context(playwright: Playwright):
    """Create browser and context with anti-detection settings"""
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US'
    )
    page = await context.new_page()
    
    # Hide webdriver features
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context, page


async def fetch_html_by_url(playwright: Playwright, url: str, target_date: datetime) -> Optional[str]:
    """Fetch HTML for bwfworldtour site using URL with specific date"""
    browser, context, page = await create_browser_context(playwright)
    
    try:
        target_url = get_date_url(url, target_date)
        await page.goto(target_url)
        await initialize_page(page)
        
        html = await get_schedule_html(page)
        
        return html
    finally:
        await context.close()
        await browser.close()


async def fetch_html_by_tab(playwright: Playwright, url: str, target_date: datetime) -> Optional[str]:
    """Fetch HTML for regular site using tab clicks with specific date"""
    browser, context, page = await create_browser_context(playwright)
    
    try:
        await page.goto(url)
        await initialize_page(page)
        
        total_dates, all_date_buttons, is_li_format = await get_date_tabs(page)
        
        if total_dates == 0:
            return None
        
        date_tab_texts = []
        for i in range(total_dates):
            try:
                tab_text = await all_date_buttons.nth(i).inner_text()
                date_tab_texts.append(tab_text.strip())
            except Exception:
                date_tab_texts.append("")
        
        target_date_index = find_date_tab_index(date_tab_texts, target_date)
        
        if target_date_index is None:
            return None
        
        button = all_date_buttons.nth(target_date_index)
        await button.click(force=True)
        await page.wait_for_timeout(1500)
        await switch_to_list_view(page)
        
        html = await get_schedule_html(page)
        
        return html
    finally:
        await context.close()
        await browser.close()


async def fetch_match_html(playwright: Playwright, url: str, target_date: datetime) -> Optional[str]:
    """
    Fetch match HTML for a specific date (automatically chooses method based on URL)
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
        target_date: Target date to scrape
        
    Returns:
        HTML string or None if not found
    """
    is_worldtour = is_bwfworldtour_url(url)
    
    if is_worldtour:
        return await fetch_html_by_url(playwright, url, target_date)
    else:
        return await fetch_html_by_tab(playwright, url, target_date)


async def fetch_all_dates_mode_max_round(playwright: Playwright, url: str) -> dict[str, str]:
    """
    Fetch mode_max_round by traversing all date tabs from first to last
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
        
    Returns:
        Dictionary with mode as key and max round (e.g., "R32") as value
    """
    mode_max_round = {}
    browser, context, page = await create_browser_context(playwright)
    
    try:
        await page.goto(url)
        await initialize_page(page)
        
        # Try to get date tabs (works for both regular and worldtour sites)
        total_dates, all_date_buttons, is_li_format = await get_date_tabs(page)
        
        if total_dates == 0:
            print(f"No date tabs found for {url}")
            return mode_max_round
        
        print(f"Found {total_dates} date tabs for {url}")
        
        # Traverse each date tab from first to last
        for i in range(total_dates):
            try:
                button = all_date_buttons.nth(i)
                await button.click(force=True)
                await page.wait_for_timeout(1500)
                await switch_to_list_view(page)
                
                html = await get_schedule_html(page)
                
                if html:
                    # Find mode_max_round for this date
                    current_round = find_mode_max_round(html)
                    
                    # Update with maximum values
                    for mode, round_str in current_round.items():
                        round_num = int(round_str[1:])
                        if mode not in mode_max_round:
                            mode_max_round[mode] = round_str
                        else:
                            existing_num = int(mode_max_round[mode][1:])
                            if round_num > existing_num:
                                mode_max_round[mode] = round_str
                    
                    print(f"Date tab {i}: found rounds {current_round}")
            except Exception as e:
                print(f"Error processing date tab {i}: {str(e)}")
                continue
        
        return mode_max_round
    finally:
        await context.close()
        await browser.close()


# ==================== Data Saving ====================

def save_match_data(
    url: str,
    level: str,
    html: str,
    mode_max_round: dict[str, str],
    target_date: datetime,
    output_dir: str,
    use_date_suffix: bool = True,
    country: str = "",
    city: str = "",
    timezone: str = ""
) -> None:
    """
    Save tournament match data for a specific date
    
    Args:
        url: Tournament URL
        level: Tournament level
        html: HTML content
        mode_max_round: Mode max round dict
        target_date: Target date
        output_dir: Output directory
        use_date_suffix: Whether to add date suffix to filename
        country: Tournament country
        city: Tournament city
        timezone: Tournament IANA timezone
    """
    os.makedirs(output_dir, exist_ok=True)
    tournament_name = extract_tournament_name(url)
    
    # Determine filename
    if use_date_suffix:
        today = datetime.now().date()
        target_date_only = target_date.date()
        
        if target_date_only == today - timedelta(days=1):
            suffix = "yesterday"
        elif target_date_only == today:
            suffix = "today"
        elif target_date_only == today + timedelta(days=1):
            suffix = "tomorrow"
        else:
            suffix = target_date.strftime("%Y-%m-%d")
        
        html_filename = f"{tournament_name}_{suffix}.html"
    else:
        html_filename = f"{tournament_name}.html"
    
    # Save HTML
    html_file = os.path.join(output_dir, html_filename)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(unidecode(html))
    
    # Save round info
    league_id = extract_league_id(url)
    league_name = format_tournament_name(tournament_name)
    age_category = "Juniors" if "junior" in level.lower() else "Adults"
    
    round_info = {
        "tournament_url": url,
        "league_id": league_id,
        "league_name": league_name,
        "level": level,
        "country": country,
        "city": city,
        "IANA_timezone": timezone,
        "age_category": age_category,
        "mode_max_round": mode_max_round,
        "target_date": target_date.strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat()
    }
    
    round_file = os.path.join(output_dir, f"{tournament_name}_round_info.json")
    with open(round_file, "w", encoding="utf-8") as f:
        json.dump(round_info, f, ensure_ascii=False, indent=2)

