"""
collector/scraper.py — Parallel article content scraper.

For each article URL, extracts a clean text excerpt using:
  1. og:title   — usually cleaner than the raw <title> tag
  2. og:description / meta description   — structured one-liner summary
  3. First meaningful paragraphs from <article>, <main>, or <body>

The combined excerpt (≤ MAX_EXCERPT chars) gives the downstream LLM
richer context than the truncated RSS summary, without sending the
entire article body.

Key improvements over the original:
  - ArticleScraper class with configurable parameters
  - Retry logic: one retry with a short backoff on transient failures
  - Fallback: if a page cannot be scraped, the RSS summary is used
    so the LLM always has *some* context to work with
  - Increased worker count and excerpt length (configured in config.py)
"""

import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from config import (
    SCRAPE_TIMEOUT,
    SCRAPE_WORKERS,
    SCRAPE_RETRIES,
    SCRAPE_RETRY_DELAY,
    MAX_BODY_CHARS,
    MAX_EXCERPT,
)

# ── Constants ────────────────────────────────────────────────────────────────

# HTTP headers that mimic a real browser to reduce bot-detection blocking.
_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# HTML tags whose text content should be skipped during body extraction
# (navigation chrome, ads, footers — not article content).
_SKIP_TAGS: frozenset[str] = frozenset({
    "script", "style", "noscript", "nav", "footer",
    "header", "aside", "form", "iframe", "button",
})

# CSS class patterns that typically indicate a main content container.
_CONTENT_CLASS_RE = re.compile(r"content|article|post|body|entry|story", re.I)


# ── ArticleScraper class ──────────────────────────────────────────────────────

class ArticleScraper:
    """
    Scrapes article pages in parallel and extracts clean text excerpts.

    All parameters default to values from config.py so callers can
    instantiate with zero arguments for the standard pipeline.

    Usage
    -----
        scraper = ArticleScraper()
        scraper.scrape_all(articles)   # fills article["scraped"] in-place
    """

    def __init__(
        self,
        timeout: float    = SCRAPE_TIMEOUT,
        max_workers: int  = SCRAPE_WORKERS,
        retries: int      = SCRAPE_RETRIES,
        retry_delay: float = SCRAPE_RETRY_DELAY,
        max_body_chars: int = MAX_BODY_CHARS,
        max_excerpt: int  = MAX_EXCERPT,
    ) -> None:
        self.timeout       = timeout
        self.max_workers   = max_workers
        self.retries       = retries
        self.retry_delay   = retry_delay
        self.max_body_chars = max_body_chars
        self.max_excerpt   = max_excerpt

    # ── Public API ────────────────────────────────────────────────────────────

    def scrape_all(self, articles: list[dict]) -> None:
        """
        Fetch all article URLs in parallel and populate each dict with a
        'scraped' key containing the extracted text excerpt.

        Falls back to the article's RSS summary when scraping fails, so
        the LLM always receives *some* context even for paywalled sources.
        Modifies article dicts in-place; returns nothing.
        """
        def _worker(article: dict) -> tuple[dict, str]:
            # Skip articles that already have scraped content (e.g. GitHub READMEs)
            if article.get("scraped"):
                return article, article["scraped"]
            return article, self.scrape_one(article["url"])

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(_worker, a): a for a in articles}
            for future in as_completed(futures):
                article, excerpt = future.result()
                if excerpt:
                    article["scraped"] = excerpt
                else:
                    # Fallback: RSS summary beats an empty string — the LLM
                    # can still make a relevance judgment from 1-2 sentences.
                    article["scraped"] = article.get("summary", "")

    def scrape_one(self, url: str) -> str:
        """
        Fetch a single URL and return a clean excerpt (≤ max_excerpt chars).

        Retries once after retry_delay seconds on any exception.
        Returns an empty string when all attempts fail (paywall, 404, timeout).
        """
        for attempt in range(self.retries + 1):
            try:
                resp = requests.get(
                    url,
                    timeout=self.timeout,
                    headers=_HEADERS,
                    allow_redirects=True,
                    stream=False,
                )
                resp.raise_for_status()

                # Skip non-HTML responses (PDFs, JSON APIs, RSS feeds, etc.)
                content_type = resp.headers.get("Content-Type", "")
                if "html" not in content_type:
                    return ""

                # Parse only the first 200 KB — fast and sufficient for metadata + intro.
                raw_html = resp.content[:200_000].decode("utf-8", errors="replace")
                return self._extract_excerpt(raw_html)

            except Exception:
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
                    continue
                return ""  # All attempts exhausted

        return ""

    # ── Private extraction helpers ────────────────────────────────────────────

    def _extract_excerpt(self, html: str) -> str:
        """
        Build an excerpt from the three content layers:
          1. og:title  →  clean canonical headline
          2. og:description or meta description  →  structured summary
          3. Body paragraphs  →  only when no description is found
        """
        soup  = BeautifulSoup(html, "html.parser")
        parts: list[str] = []

        # Layer 1: Canonical title from Open Graph (often cleaner than <title>)
        og_title   = self._og(soup, "og:title")
        page_title = og_title or self._tag_text(soup.find("title"))
        if page_title:
            parts.append(page_title[:120])

        # Layer 2: Structured description (high signal, written by the publisher)
        og_desc = (
            self._og(soup, "og:description")
            or self._meta_name(soup, "description")
        )
        if og_desc:
            parts.append(og_desc[:400])

        # Layer 3: Raw body paragraphs — only when no structured description exists.
        # Avoids duplicating the description text in the final excerpt.
        if not og_desc:
            body_text = self._body_text(soup)
            if body_text:
                parts.append(body_text[: self.max_body_chars])

        excerpt = " | ".join(p.strip() for p in parts if p.strip())
        return excerpt[: self.max_excerpt]

    def _body_text(self, soup: BeautifulSoup) -> str:
        """
        Walk progressively broader content containers until we find enough
        paragraph text. Skips navigation/chrome tags defined in _SKIP_TAGS.
        Minimum paragraph length of 40 chars filters out "Read more" snippets.
        """
        containers = [
            soup.find("article"),
            soup.find("main"),
            soup.find("div", attrs={"class": _CONTENT_CLASS_RE}),
            soup.find("body"),
        ]
        for container in containers:
            if not container:
                continue

            paragraphs: list[str] = []
            for tag in container.find_all(["p", "li"], recursive=True):
                # Skip text inside navigation / UI chrome
                if tag.find_parent(_SKIP_TAGS):
                    continue
                text = tag.get_text(" ", strip=True)
                if len(text) >= 40:
                    paragraphs.append(text)
                if sum(len(p) for p in paragraphs) >= self.max_body_chars:
                    break

            if paragraphs:
                return " ".join(paragraphs)

        return ""

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _og(soup: BeautifulSoup, prop: str) -> str:
        """Extract the content= attribute of an Open Graph <meta> tag."""
        tag = soup.find("meta", attrs={"property": prop})
        return (tag.get("content") or "").strip() if tag else ""

    @staticmethod
    def _meta_name(soup: BeautifulSoup, name: str) -> str:
        """Extract the content= attribute of a named <meta> tag."""
        tag = soup.find("meta", attrs={"name": name})
        return (tag.get("content") or "").strip() if tag else ""

    @staticmethod
    def _tag_text(tag) -> str:
        """Return stripped text content of a BeautifulSoup tag, or ''."""
        return tag.get_text(strip=True) if tag else ""


# ── Module-level convenience wrapper (backward-compatible) ───────────────────

def scrape_all_parallel(articles: list[dict]) -> None:
    """
    Backward-compatible wrapper used by existing call sites in ranker.py.
    Creates a default ArticleScraper and scrapes all articles in-place.
    """
    ArticleScraper().scrape_all(articles)
