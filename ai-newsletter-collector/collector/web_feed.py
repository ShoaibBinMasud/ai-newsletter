"""
collector/web_feed.py — Direct blog page scraper for AI companies without RSS feeds.

Fetches blog/news listing pages and extracts article links + publication dates.
Acts as a second layer on top of RSS: catches official announcements the same day
they're published, before they're indexed by Google News or covered by tech press.

Date extraction strategies (tried in order):
  1. JSON-LD structured data  — <script type="application/ld+json"> with datePublished
  2. <time datetime="...">    — HTML5 time elements with machine-readable dates
  3. Text pattern matching    — scans text near article links for date-like strings

Articles with no parseable date are dropped (same rule as RSS pipeline).
Articles outside the current edition dates are dropped.

Falls back silently per source — a 403 or parse failure skips that source
without breaking the rest of the pipeline.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urljoin

from collector.rss import get_edition_dates
from config import ARTICLE_FILTER_MODE, LOOKBACK_HOURS


# =============================================================================
# HTTP session
# =============================================================================

_TIMEOUT = 10  # seconds

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Links containing these strings are navigation/social — not articles
_SKIP_HREF = ("twitter.com", "linkedin", "facebook.com", "youtube", "instagram",
              "mailto:", "javascript:", "#", "/cdn-cgi/")


# =============================================================================
# Date parsing
# =============================================================================

_MONTH_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date(text: str) -> Optional[date]:
    """
    Parse a date string into a date object.

    Handles:
      - ISO:              2026-03-18  (or datetime prefix 2026-03-18T...)
      - Long month:       March 18, 2026
      - Short month:      Mar 16, 2026
    """
    text = text.strip()
    # ISO / datetime prefix
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # "Month DD, YYYY"  or  "Mon DD, YYYY"
    m = re.search(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", text)
    if m:
        month = _MONTH_MAP.get(m.group(1).lower()[:3])
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(2)))
            except ValueError:
                pass
    return None


# =============================================================================
# Extraction strategies
# =============================================================================

def _from_json_ld(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Extract articles from JSON-LD structured data.

    Looks for @type values of Article, BlogPosting, or NewsArticle.
    Handles both single-object and @graph array formats.
    """
    results = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        items = (
            data.get("@graph", [data]) if isinstance(data, dict) else data
        )
        if not isinstance(items, list):
            items = [items]

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") not in ("Article", "BlogPosting", "NewsArticle"):
                continue

            url_raw = (
                item.get("url")
                or (item.get("mainEntityOfPage") or {}).get("@id", "")
            )
            title    = (item.get("headline") or item.get("name", "")).strip()
            date_str = item.get("datePublished", "")
            pub_date = _parse_date(date_str)

            if url_raw and title and pub_date:
                results.append({
                    "title":    title,
                    "url":      urljoin(base_url, url_raw),
                    "pub_date": pub_date,
                })

    return results


def _from_time_elements(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Extract articles by finding <time> elements and walking up to find article links.

    Each <time> element must be inside (or near) an <a> tag whose href looks like
    an article path (not a nav or social link).
    """
    results = []
    seen_urls: set[str] = set()

    for time_el in soup.find_all("time"):
        datetime_attr = time_el.get("datetime", "")
        pub_date = _parse_date(datetime_attr) or _parse_date(time_el.get_text())
        if not pub_date:
            continue

        # Walk up ancestors to find the nearest enclosing <a>
        link_tag = None
        for ancestor in time_el.parents:
            if ancestor.name == "a" and ancestor.get("href"):
                link_tag = ancestor
                break
            # Also check direct children <a> within the same card
            a = ancestor.find("a", href=True)
            if a:
                link_tag = a
                break
            if ancestor.name in ("body", "html"):
                break

        if not link_tag:
            continue

        href = link_tag.get("href", "")
        if any(s in href for s in _SKIP_HREF):
            continue

        url = urljoin(base_url, href)
        if url in seen_urls:
            continue

        title = link_tag.get_text(strip=True)[:200]
        if not title or len(title) < 10:
            # Try the heading inside the card
            card = link_tag.parent
            if card:
                h = card.find(re.compile(r"^h[1-6]$"))
                title = h.get_text(strip=True) if h else title

        if title:
            seen_urls.add(url)
            results.append({"title": title, "url": url, "pub_date": pub_date})

    return results


def _from_date_text(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Last-resort: scan all text nodes for date-like strings and find a nearby link.

    Only fires if the two strategies above returned nothing.
    """
    results = []
    seen_urls: set[str] = set()

    date_pattern = re.compile(
        r"\b(?:[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})\b"
    )

    for el in soup.find_all(string=date_pattern):
        pub_date = _parse_date(date_pattern.search(el).group())
        if not pub_date:
            continue

        # Find an <a> in the same parent block
        parent = el.parent
        for _ in range(4):          # look up to 4 levels up
            if parent is None:
                break
            a = parent.find("a", href=True)
            if a:
                href = a["href"]
                if any(s in href for s in _SKIP_HREF):
                    break
                url = urljoin(base_url, href)
                if url not in seen_urls:
                    title = a.get_text(strip=True)[:200]
                    if title and len(title) >= 10:
                        seen_urls.add(url)
                        results.append({"title": title, "url": url, "pub_date": pub_date})
                break
            parent = parent.parent

    return results


# =============================================================================
# Per-source fetcher
# =============================================================================

def _scrape_source(name: str, page_url: str) -> list[dict]:
    """
    Fetch a single blog listing page and return raw extracted articles.

    Each article dict has: title, url, pub_date (date object).
    Returns [] on any network or parse error.
    """
    try:
        resp = requests.get(page_url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  [web] Skip {name}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    articles = _from_json_ld(soup, page_url)
    if not articles:
        articles = _from_time_elements(soup, page_url)
    if not articles:
        articles = _from_date_text(soup, page_url)

    return articles


# =============================================================================
# Public API
# =============================================================================

def fetch_web_sources(
    web_sources: list[tuple[str, str]],
    edition_dates: Optional[frozenset] = None,
) -> list[dict]:
    """
    Scrape all web sources and return articles filtered to edition dates.

    Parameters
    ----------
    web_sources   : list of (name, page_url)
    edition_dates : frozenset of date — defaults to get_edition_dates()

    Returns
    -------
    Flat list of article dicts (same format as rss.fetch_feed, no sector key)
    """
    # Determine the cutoff based on filter mode
    if ARTICLE_FILTER_MODE == "hours":
        cutoff_date = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).date()
        edition_dates = None
    else:
        if edition_dates is None:
            edition_dates = get_edition_dates()
        cutoff_date = None

    results: list[dict] = []

    for name, page_url in web_sources:
        raw = _scrape_source(name, page_url)
        if cutoff_date is not None:
            kept = [a for a in raw if a["pub_date"] >= cutoff_date]
        else:
            kept = [a for a in raw if a["pub_date"] in edition_dates]

        for a in kept:
            pub_dt = datetime.combine(a["pub_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
            results.append({
                "title":        a["title"],
                "url":          a["url"],
                "source":       name,
                "summary":      "",
                "published_at": pub_dt.isoformat(),
                "is_github":    0,
                "stars":        None,
                "feed_mentions": 1,
            })

        if kept:
            print(f"  [web] {name}: {len(kept)} article(s)")

    if results:
        print(f"  Web scraper total: {len(results)} article(s)")

    return results
