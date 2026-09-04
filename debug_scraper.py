"""
Debug script — run this in your django_web_scraper directory
with the venv activated to diagnose scraping issues.

Usage:
    python debug_scraper.py
"""

import sys
print(f"Python: {sys.version}")

# Test requests
try:
    import requests
    print(f"requests: OK ({requests.__version__})")
except ImportError as e:
    print(f"requests: MISSING — {e}")

# Test BeautifulSoup
try:
    from bs4 import BeautifulSoup
    print(f"beautifulsoup4: OK")
except ImportError as e:
    print(f"beautifulsoup4: MISSING — {e}")

# Test lxml
try:
    import lxml
    print(f"lxml: OK ({lxml.__version__})")
    PARSER = 'lxml'
except ImportError:
    print(f"lxml: NOT INSTALLED — will use html.parser instead")
    PARSER = 'html.parser'

print(f"\nUsing parser: {PARSER}")
print("-" * 60)

# Fetch quotes.toscrape.com
URL = "https://quotes.toscrape.com"
print(f"\nFetching: {URL}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}

try:
    r = requests.get(URL, headers=headers, timeout=15)
    print(f"Status code: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
    print(f"Content length: {len(r.content)} bytes")
    print(f"Encoding: {r.encoding}")
except Exception as e:
    print(f"FETCH FAILED: {e}")
    sys.exit(1)

print("-" * 60)

# Parse with BeautifulSoup
soup = BeautifulSoup(r.content, PARSER)

# Show page title
title = soup.title.string if soup.title else "(no title)"
print(f"\nPage title: {title}")

# Try various selectors
selectors_to_test = [
    'span.text',
    '.text',
    '.quote',
    '.quote .text',
    'span[class]',
    'div.quote span',
    'span',
    'div',
]

print("\n--- Selector Test Results ---")
for sel in selectors_to_test:
    try:
        matches = soup.select(sel)
        if matches:
            preview = matches[0].get_text(strip=True)[:60]
            print(f"  {sel!r:30s}  → {len(matches)} matches  | first: {preview!r}")
        else:
            print(f"  {sel!r:30s}  → 0 matches")
    except Exception as e:
        print(f"  {sel!r:30s}  → ERROR: {e}")

print("\n--- First 500 chars of raw HTML ---")
print(r.text[:500])
print("...")
