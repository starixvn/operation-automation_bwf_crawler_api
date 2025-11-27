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
from fastapi import HTTPException


# ==================== URL & Name Processing ====================

def normalize_tournament_name(tournament_name: str) -> str:
    """
    Normalize tournament name to pure English with Title Case
    
    Converts non-English characters to English using unidecode,
    removes non-alphabetic characters (except spaces),
    and capitalizes the first letter of each word.
    Preserves Roman numerals (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
    
    Args:
        tournament_name: Tournament name (may contain non-English characters)
        
    Returns:
        Normalized tournament name in Title Case with only English characters
    """
    if not tournament_name:
        return tournament_name
    
    # Convert to ASCII/English using unidecode
    name = unidecode(tournament_name)
    
    # Remove non-alphabetic characters except spaces
    name = re.sub(r'[^a-zA-Z\s]', ' ', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    # Strip leading/trailing spaces
    name = name.strip()
    
    # Split into words and process each word
    words = name.split()
    processed_words = []
    
    # Pattern to match Roman numerals (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
    roman_pattern = re.compile(r'^[IVX]+$', re.IGNORECASE)
    
    for word in words:
        # Check if word is a Roman numeral
        if roman_pattern.match(word):
            # Keep Roman numeral in uppercase
            processed_words.append(word.upper())
        else:
            # Apply title case to regular words
            processed_words.append(word.title())
    
    # Join words back together
    name = ' '.join(processed_words)
    
    return name


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
        print("Closed popup window")
    except Exception:
        print("No popup window to close")
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
    await page.wait_for_timeout(3000)
    await switch_to_list_view(page)


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
    
    # Get cookies from JSON file
    cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'BWF_cookies.json')
    cookies_data = None
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        print(f"Loaded {len(cookies_data)} cookies from {cookie_file}")
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US'
    )
    
    # Add cookies to browser cookie store
    if cookies_data:
        await context.add_cookies(cookies_data)
        print("Added cookies to browser")
    
    page = await context.new_page()
    
    # Hide webdriver features
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context, page


async def fetch_response_by_url(playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
    """Fetch Web response for regular site using goint to the specific date url"""
    browser, context, page = await create_browser_context(playwright)
    
    try:
        result = []
        async def log_response(response):
            if (response.url == api_url):
                result.append(await response.json())

        page.on("response", log_response)

        target_url = get_date_url(url, target_date)

        await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
        await initialize_page(page)
        await page.wait_for_timeout(2500)

        return result[0]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get match info: {str(e)}"
        )

    finally:
        await context.close()
        await browser.close()


async def fetch_response_by_tab(playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
    """Fetch Web response for regular site using tab clicks with specific date"""
    browser, context, page = await create_browser_context(playwright)
    
    try:
        result = []
        async def log_response(response):
            if (response.url == api_url):
                result.append(await response.json())

        page.on("response", log_response)

        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await initialize_page(page)        
        
        total_dates, all_date_buttons, is_li_format = await get_date_tabs(page)
    
        if total_dates == 0:
            return None
        
        date_tab_texts = []
        for i in range(total_dates):
            try:
                element = all_date_buttons.nth(i)
                key = await element.inner_text()
                date_tab_texts.append(key.strip())
            except Exception:
                date_tab_texts.append("")

        target_date_index = find_date_tab_index(date_tab_texts, target_date)
        
        if target_date_index is None:
            return None
        
        button = all_date_buttons.nth(target_date_index)
        await button.click(force=True)
        await page.wait_for_timeout(2500)
        await switch_to_list_view(page)

        return result[0]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get match info: {str(e)}"
        )

    finally:
        await context.close()
        await browser.close()


async def fetch_match_response(playwright: Playwright, url: str, target_date: datetime, api_url: str) -> Optional[str]:
    """
    Fetch match Web response for a specific date (automatically chooses method based on URL)
    
    Args:
        playwright: Playwright instance
        url: Tournament URL
        target_date: Target date to scrape
        api_url: Target response api url
        
    Returns:
        Matches information or None if not found
    """
    is_worldtour = is_bwfworldtour_url(url)
    
    if is_worldtour:
        return await fetch_response_by_url(playwright, url, target_date, api_url)
    else:
        return await fetch_response_by_tab(playwright, url, target_date, api_url)

