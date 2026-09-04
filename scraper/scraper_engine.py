"""
Core scraping engine using requests + BeautifulSoup4.
Handles fetching, parsing, retry logic, and user-agent rotation.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# User-Agent pool for basic bot-detection avoidance
# ──────────────────────────────────────────────────────────────────────────────
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0',
]

DEFAULT_TIMEOUT = 15          # seconds per request
MAX_RETRIES = 3               # number of retry attempts
RETRY_BACKOFF = 2.0           # seconds between retries (doubles each attempt)


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class ScrapedElement:
    """Represents a single scraped element from a page."""
    index: int
    tag: str
    content: str


@dataclass
class ScrapeResponse:
    """Full result of a scrape operation."""
    success: bool
    url: str
    elements: List[ScrapedElement] = field(default_factory=list)
    error: str = ''
    status_code: Optional[int] = None
    page_title: str = ''


# ──────────────────────────────────────────────────────────────────────────────
# Main scraper engine
# ──────────────────────────────────────────────────────────────────────────────
def _build_headers(extra_headers: dict) -> dict:
    """Build request headers with a random user-agent."""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    headers.update(extra_headers)
    return headers


def _fetch_page(url: str, headers: dict) -> requests.Response:
    """
    Fetch a URL with retry logic and exponential back-off.
    Raises requests.RequestException on final failure.
    """
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Fetching %s (attempt %d/%d)", url, attempt, MAX_RETRIES)
            response = requests.get(
                url,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                sleep_time = RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning("Attempt %d failed: %s. Retrying in %.1fs…", attempt, exc, sleep_time)
                time.sleep(sleep_time)

    raise last_exc


def _extract_content(element, attribute: str) -> str:
    """
    Extract content from a BeautifulSoup Tag.
    - attribute='text'  → get_text() stripped
    - anything else     → get the HTML attribute value (e.g. 'href', 'src')
    """
    if attribute.lower() == 'text':
        return element.get_text(separator=' ', strip=True)
    value = element.get(attribute, '')
    return str(value).strip() if value else ''


def scrape_url(
    url: str,
    css_selector: str,
    extract_attribute: str = 'text',
    extra_headers: Optional[dict] = None,
) -> ScrapeResponse:
    """
    Main entry point for scraping.

    Args:
        url:               Target URL to scrape.
        css_selector:      CSS selector string (e.g. 'h1', '.product-title', 'a.link').
        extract_attribute: 'text' for inner text, or any HTML attribute like 'href', 'src'.
        extra_headers:     Optional dict of additional HTTP request headers.

    Returns:
        ScrapeResponse with success flag, elements list, or error details.
    """
    if extra_headers is None:
        extra_headers = {}

    headers = _build_headers(extra_headers)

    # ── Fetch ──────────────────────────────────────────────────────────────────
    try:
        response = _fetch_page(url, headers)
    except requests.exceptions.ConnectionError:
        return ScrapeResponse(success=False, url=url, error='Connection error: Could not reach the server.')
    except requests.exceptions.Timeout:
        return ScrapeResponse(success=False, url=url, error=f'Timeout: Server did not respond within {DEFAULT_TIMEOUT}s.')
    except requests.exceptions.HTTPError as exc:
        return ScrapeResponse(
            success=False, url=url,
            error=f'HTTP error: {exc.response.status_code} {exc.response.reason}',
            status_code=exc.response.status_code,
        )
    except requests.RequestException as exc:
        return ScrapeResponse(success=False, url=url, error=f'Request error: {exc}')

    # ── Parse ──────────────────────────────────────────────────────────────────
    # Use response.text (pre-decoded Unicode string) instead of response.content
    # (raw bytes) to avoid lxml encoding errors on special characters like
    # curly quotes (\u201c \u201d) that trip up the lxml XML byte-stream parser.
    if not response.encoding:
        response.encoding = 'utf-8'
    html_text = response.text

    # Use html.parser (Python built-in) — avoids lxml encoding errors
    # with special Unicode characters (curly quotes, em-dashes, etc.)
    if not response.encoding:
        response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')


    page_title = soup.title.string.strip() if soup.title and soup.title.string else ''

    # ── Select elements ────────────────────────────────────────────────────────
    try:
        matched_elements = soup.select(css_selector)
    except Exception as exc:
        return ScrapeResponse(
            success=False, url=url,
            error=f'Invalid CSS selector "{css_selector}": {exc}',
            status_code=response.status_code,
            page_title=page_title,
        )

    if not matched_elements:
        return ScrapeResponse(
            success=True, url=url,
            elements=[],
            status_code=response.status_code,
            page_title=page_title,
            error=f'No elements matched selector "{css_selector}".',
        )

    # ── Extract content ────────────────────────────────────────────────────────
    scraped = []
    for idx, el in enumerate(matched_elements):
        content = _extract_content(el, extract_attribute)
        if content:  # skip blank/empty values
            scraped.append(ScrapedElement(index=idx, tag=el.name or '', content=content))

    logger.info("Scraped %d elements from %s", len(scraped), url)

    return ScrapeResponse(
        success=True,
        url=url,
        elements=scraped,
        status_code=response.status_code,
        page_title=page_title,
    )