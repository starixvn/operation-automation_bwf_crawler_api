import re
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page, Playwright, async_playwright

DEFAULT_TOURNAMENT_LIST = [
    "https://bwfbadminton.com/tournament/5263/yonex-sunrise-bwf-world-junior-mixed-team-championships-2025",
    "https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/",
    "https://bwfbadminton.com/tournament/5331/africa-para-badminton-championships-2025",
    "https://bwfbadminton.com/tournament/5408/victor-turkiye-international-challenge-2025",
    "https://bwfbadminton.com/tournament/5412/roketto-sydney-international-2025",
    "https://bwfbadminton.com/tournament/5522/algeria-international-2025"
]


def find_max_round(html: str) -> Optional[int]:
    """
    Find the maximum R number from HTML (e.g., R32, R64, R128...)
    Excludes qualification formats like "Qual. R16"

    Args:
        html: HTML content of the schedule

    Returns:
        Maximum R number, or None if not found
    """
    # Find all footer-label contents, then filter for pure R+number format
    all_labels = re.findall(r'<span class="footer-label">\s*([^<]+?)\s*</span>', html)

    round_numbers = []
    for label in all_labels:
        # Only match pure R+number format, excluding other text
        match = re.match(r'^R(\d+)$', label.strip())
        if match:
            round_num = int(match.group(1))
            round_numbers.append(round_num)

    if round_numbers:
        max_round = max(round_numbers)
        return max_round
    else:
        return None


async def close_popup_if_exists(page: Page) -> None:
    """Close popup window if exists"""
    try:
        await page.get_by_role("button", name="Close").click()
    except Exception:
        pass


async def get_date_tabs(page: Page) -> tuple[int, any, bool]:
    """
    Get all date tabs, exclude PODIUM tab
    Supports two formats:
    1. .container-fullwidth > .page-tab-wrapper-outer (button/div)
    2. ul#ajaxTabsResults.days-tabs > li

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

    # Check if last tab is PODIUM and exclude it
    last_tab_text = await all_date_buttons.nth(total_tabs - 1).inner_text()
    if "PODIUM" in last_tab_text.upper():
        total_dates = total_tabs - 1
    else:
        total_dates = total_tabs

    return total_dates, all_date_buttons, is_li_format


async def switch_to_list_view(page: Page) -> None:
    """Switch to List View (if not already in List View)"""
    try:
        await page.locator("label").filter(has_text="List View").locator("span").click(force=True, timeout=5000)
        await page.wait_for_timeout(1000)
    except Exception:
        pass


async def initialize_page(page: Page) -> None:
    """
    Initialize page: close popup, wait for loading, switch to List View

    Args:
        page: Playwright page object
    """
    await close_popup_if_exists(page)
    await page.wait_for_timeout(2000)
    await switch_to_list_view(page)


async def get_schedule_html(page: Page) -> Optional[str]:
    """
    Get schedule HTML from current page

    Returns:
        HTML string, or None if no content
    """
    if await page.get_by_role("heading", name="No schedule announced").count() > 0:
        return None

    if await page.locator(".container.results-wrapper").count() == 0:
        return None

    try:
        await page.wait_for_selector(".container.results-wrapper", timeout=3000)
        await page.wait_for_timeout(500)  # Extra wait to ensure content fully loaded
    except Exception:
        return None

    return await page.locator(".container.results-wrapper").evaluate("el => el.outerHTML")


async def find_first_valid_round(page: Page, total_dates: int, all_date_buttons) -> tuple[Optional[int], Optional[int]]:
    """
    Iterate all date tabs, find first date with R+number content

    Returns:
        tuple[Optional[int], Optional[int]]: (max round number, current date index)
    """
    for date_index in range(total_dates):
        button = all_date_buttons.nth(date_index)
        await button.click(force=True)
        await page.wait_for_timeout(2000)

        await switch_to_list_view(page)

        html = await get_schedule_html(page)
        if html is None:
            continue

        max_round = find_max_round(html)
        if max_round is not None:
            return max_round, date_index

    return None, None


def format_date_string(date: datetime) -> tuple[str, str, str, str]:
    """
    Format date to multiple formats
    Supports: "02 OCT", "2 OCT", "02 Oct", "2 Oct"

    Returns:
        tuple[str, str, str, str]: (uppercase with zero, uppercase without zero, title case with zero, title case without zero)
    """
    upper_with_zero = date.strftime("%d %b").upper()
    upper_without_zero = date.strftime("%-d %b" if date.day < 10 else "%d %b").upper()
    title_with_zero = date.strftime("%d %b")
    title_without_zero = date.strftime("%-d %b" if date.day < 10 else "%d %b")

    return upper_with_zero, upper_without_zero, title_with_zero, title_without_zero


def find_date_tab_index(date_tab_texts: list[str], target_date: datetime) -> Optional[int]:
    """
    Find index of specified date in tab text list
    Supports multiple date formats: "02 OCT", "2 OCT", "02 Oct", "2 Oct"

    Args:
        date_tab_texts: all tab text list
        target_date: target date

    Returns:
        Found index, or None if not found
    """
    upper_with_zero, upper_without_zero, title_with_zero, title_without_zero = format_date_string(target_date)

    for i, tab_text in enumerate(date_tab_texts):
        if (upper_with_zero in tab_text or
            upper_without_zero in tab_text or
            title_with_zero in tab_text or
            title_without_zero in tab_text):
            return i

    return None


async def extract_html_for_date(page: Page, all_date_buttons, date_index: int, date_label: str, skip_list_view: bool = False) -> Optional[str]:
    """
    Click specified date tab and extract HTML

    Args:
        page: Playwright page object
        all_date_buttons: locator for all date buttons
        date_index: tab index to click
        date_label: date label (for logging)
        skip_list_view: whether to skip switch to List View (if already in List View)

    Returns:
        HTML string, or None if no content
    """
    button = all_date_buttons.nth(date_index)
    await button.click(force=True)
    await page.wait_for_timeout(1500)

    if not skip_list_view:
        await switch_to_list_view(page)

    html = await get_schedule_html(page)

    return html


async def collect_today_tomorrow_schedules(page: Page, all_date_buttons, total_dates: int, current_date_index: Optional[int] = None) -> dict[str, str]:
    """
    Collect today and tomorrow schedule HTML

    Args:
        page: Playwright page object
        all_date_buttons: locator for all date buttons
        total_dates: date tab total count
        current_date_index: Current date index (if known)

    Returns:
        dict: {"today": html, "tomorrow": html}
    """
    total_dates_updated, all_date_buttons_updated, is_li = await get_date_tabs(page)

    date_tab_texts = []
    for i in range(total_dates):
        try:
            tab_text = await all_date_buttons_updated.nth(i).inner_text()
            date_tab_texts.append(tab_text.strip())
        except Exception:
            date_tab_texts.append("")

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    today_index = find_date_tab_index(date_tab_texts, today)
    tomorrow_index = find_date_tab_index(date_tab_texts, tomorrow)

    html_results = {}

    if today_index is not None:
        # If already on today's date page, extract HTML directly
        if current_date_index == today_index:
            today_html = await get_schedule_html(page)
            if today_html:
                html_results["today"] = today_html
        else:
            today_html = await extract_html_for_date(page, all_date_buttons, today_index, "today", skip_list_view=False)
            if today_html:
                html_results["today"] = today_html
                current_date_index = today_index

    if tomorrow_index is not None:
        # If already on tomorrow's date page, extract HTML directly
        if current_date_index == tomorrow_index:
            tomorrow_html = await get_schedule_html(page)
            if tomorrow_html:
                html_results["tomorrow"] = tomorrow_html
        else:
            # If already got today's data, already in List View, skip switching
            skip_list_view = "today" in html_results
            tomorrow_html = await extract_html_for_date(page, all_date_buttons, tomorrow_index, "tomorrow", skip_list_view=skip_list_view)
            if tomorrow_html:
                html_results["tomorrow"] = tomorrow_html

    return html_results


def extract_tournament_name(url: str) -> str:
    """
    Extract tournament name from URL

    Args:
        url: tournament URL

    Returns:
        Tournament name

    Examples:
        - https://bwfbadminton.com/tournament/5263/yonex-sunrise-bwf-world-junior-mixed-team-championships-2025
          -> yonex-sunrise-bwf-world-junior-mixed-team-championships-2025
        - https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/
          -> clash-of-clans-arctic-open-2025-powered-by-yonex
        - https://bwfworldtour.bwfbadminton.com/tournament/5287/clash-of-clans-arctic-open-2025-powered-by-yonex/results/2025-10-08
          -> clash-of-clans-arctic-open-2025-powered-by-yonex
    """
    url = re.sub(r'/\d{4}-\d{2}-\d{2}/?$', '', url)
    url = re.sub(r'/results/?$', '', url)
    url = url.rstrip('/')
    tournament_name = url.split("/")[-1]
    return tournament_name


def save_tournament_data(url: str, max_round: int, html_results: dict[str, str], output_dir: str = "two_days") -> None:
    """
    Save tournament data to specified folder

    Args:
        url: tournament URL
        max_round: Maximum round number
        html_results: {"today": html, "tomorrow": html}
        output_dir: output directory path
    """
    os.makedirs(output_dir, exist_ok=True)
    tournament_name = extract_tournament_name(url)

    if "today" in html_results:
        today_file = os.path.join(output_dir, f"{tournament_name}_today.html")
        with open(today_file, "w", encoding="utf-8") as f:
            f.write(html_results["today"])

    if "tomorrow" in html_results:
        tomorrow_file = os.path.join(output_dir, f"{tournament_name}_tomorrow.html")
        with open(tomorrow_file, "w", encoding="utf-8") as f:
            f.write(html_results["tomorrow"])

    round_info = {
        "tournament_url": url,
        "tournament_name": tournament_name,
        "max_round": max_round,
        "timestamp": datetime.now().isoformat()
    }
    round_file = os.path.join(output_dir, f"{tournament_name}_round_info.json")
    with open(round_file, "w", encoding="utf-8") as f:
        json.dump(round_info, f, ensure_ascii=False, indent=2)


async def fetch_schedule_from_url(playwright: Playwright, url: str, date_label: str = "") -> Optional[str]:
    """
    Get schedule HTML from specified URL (unified browser operation function)

    Args:
        playwright: Playwright instance
        url: complete URL (with date)
        date_label: date label (for logging)

    Returns:
        HTML string, or None if no content
    """
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
    await page.goto(url)

    await initialize_page(page)

    html = await get_schedule_html(page)

    await context.close()
    await browser.close()

    return html


async def collect_schedules_by_url(playwright: Playwright, base_url: str, output_dir: str) -> dict[str, str]:
    """
    Use URL to switch dates and collect today and tomorrow schedules (for bwfworldtour website)

    Args:
        playwright: Playwright instance
        base_url: Base URL
        output_dir: output directory path

    Returns:
        dict: {"today": html, "tomorrow": html}
    """
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    html_results = {}

    today_url = get_date_url(base_url, today)
    today_html = await fetch_schedule_from_url(playwright, today_url, "today")
    if today_html:
        html_results["today"] = today_html

    tomorrow_url = get_date_url(base_url, tomorrow)
    tomorrow_html = await fetch_schedule_from_url(playwright, tomorrow_url, "tomorrow")
    if tomorrow_html:
        html_results["tomorrow"] = tomorrow_html

    return html_results


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


def extract_dates_from_tabs(date_tab_texts: list[str]) -> list[datetime]:
    """
    Extract dates from tab texts

    Args:
        date_tab_texts: all tab text list

    Returns:
        date list
    """
    dates = []
    current_year = datetime.now().year

    for tab_text in date_tab_texts:
        match = re.search(r'(\d{1,2})\s+([A-Za-z]{3})', tab_text)
        if match:
            day = int(match.group(1))
            month_str = match.group(2).upper()

            month_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }

            if month_str in month_map:
                month = month_map[month_str]
                try:
                    date_obj = datetime(current_year, month, day)
                    dates.append(date_obj)
                except ValueError:
                    pass

    return dates


async def find_first_valid_round_by_url(playwright: Playwright, base_url: str, dates: list[datetime]) -> tuple[Optional[int], Optional[datetime]]:
    """
    Use URL to switch dates, find first date with R+number content (for bwfworldtour website)

    Args:
        playwright: Playwright instance
        base_url: Base URL
        dates: Date list to check

    Returns:
        tuple[Optional[int], Optional[datetime]]: (max round number, found date)
    """
    for date in dates:
        date_url = get_date_url(base_url, date)

        html = await fetch_schedule_from_url(playwright, date_url)

        if html is None:
            continue

        max_round = find_max_round(html)
        if max_round is not None:
            return max_round, date

    return None, None


async def get_date_tab_texts(page: Page) -> tuple[list[str], int, any, bool]:
    """
    Get date tab text list

    Args:
        page: Playwright page object

    Returns:
        tuple: (tab text list, tab count, tab button locator, whether li format)
    """
    total_dates, all_date_buttons, is_li_format = await get_date_tabs(page)

    date_tab_texts = []
    for i in range(total_dates):
        try:
            tab_text = await all_date_buttons.nth(i).inner_text()
            date_tab_texts.append(tab_text.strip())
        except Exception:
            date_tab_texts.append("")

    return date_tab_texts, total_dates, all_date_buttons, is_li_format


async def find_max_round_for_tournament(
    playwright: Playwright,
    url: str,
    page: Page,
    date_tab_texts: list[str],
    total_dates: int,
    all_date_buttons,
    is_worldtour: bool
) -> tuple[Optional[int], Optional[int], Optional[datetime]]:
    """
    Find tournament max round

    Args:
        playwright: Playwright instance
        url: tournament URL
        page: Playwright page object (only for non-worldtour)
        date_tab_texts: date tab text list
        total_dates: date tab total count
        all_date_buttons: date button locator (only for non-worldtour)
        is_worldtour: whether is bwfworldtour website

    Returns:
        tuple: (max round, current date index, found date)
    """
    if is_worldtour:
        # bwfworldtour website: use URL to switch dates
        dates = extract_dates_from_tabs(date_tab_texts)
        max_round, found_date = await find_first_valid_round_by_url(playwright, url, dates)
        return max_round, None, found_date
    else:
        # Regular website: use tab clicks
        max_round, current_date_index = await find_first_valid_round(page, total_dates, all_date_buttons)
        return max_round, current_date_index, None


async def run(playwright: Playwright, url: str, output_dir: str = "two_days") -> None:
    """
    Main process for handling single tournament

    Args:
        playwright: Playwright instance
        url: tournament URL
        output_dir: output directory path
    """
    is_worldtour = is_bwfworldtour_url(url)

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
    await page.goto(url)

    await initialize_page(page)

    date_tab_texts, total_dates, all_date_buttons, is_li_format = await get_date_tab_texts(page)

    if total_dates == 0:
        await context.close()
        await browser.close()
        return

    if is_worldtour:
        await context.close()
        await browser.close()

    max_round, current_date_index, found_date = await find_max_round_for_tournament(
        playwright, url, page, date_tab_texts, total_dates, all_date_buttons, is_worldtour
    )

    if max_round is None:
        max_round = 0

    if is_worldtour:
        html_results = await collect_schedules_by_url(playwright, url, output_dir)
    else:
        html_results = await collect_today_tomorrow_schedules(page, all_date_buttons, total_dates, current_date_index)

    if html_results:
        save_tournament_data(url, max_round, html_results, output_dir)

    if not is_worldtour:
        await context.close()
        await browser.close()


async def main(playwright: Playwright, tournament_list: list[str] = None, output_dir: str = "two_days") -> None:
    """
    Main program entry

    Args:
        playwright: Playwright instance
        tournament_list: tournament URL list, use default list if not provided
        output_dir: output directory path
    """
    if tournament_list is None:
        tournament_list = DEFAULT_TOURNAMENT_LIST

    for url in tournament_list:
        if re.search(r'[-/]para[-/]', url.lower()):
            continue

        await run(playwright, url, output_dir)


if __name__ == "__main__":
    async def entry():
        async with async_playwright() as playwright:
            await main(playwright, DEFAULT_TOURNAMENT_LIST, "two_days")

    asyncio.run(entry())