"""
collector/hf_papers.py — Scrape the #1 trending paper from Trending Papers.

Fetches https://huggingface.co/papers/trending, takes the top paper,
then scrapes its individual page for the abstract and any linked GitHub repo.

Returns a single article dict with:
  - url        : HuggingFace paper page (https://huggingface.co/papers/{id})
  - github_url : GitHub repo link if listed on the paper page (may be None)
  - is_github  : 1  (so it bypasses the editorial filter like Trending Repos & Papers)
  - summary/scraped : abstract text
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


HF_TRENDING_URL = "https://huggingface.co/papers/trending"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_GITHUB_RE = re.compile(r"https?://github\.com/[\w\-]+/[\w\-\.]+", re.I)


def _scrape_paper_page(paper_url: str) -> tuple[str, str | None]:
    """
    Fetch an individual HF paper page.
    Returns (abstract_text, github_repo_url_or_None).
    """
    try:
        resp = requests.get(paper_url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Abstract — find the longest <p> on the page (HF renders it as plain text)
        abstract = ""
        paragraphs = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 100
        ]
        if paragraphs:
            abstract = max(paragraphs, key=len)[:800]

        # GitHub link — scan all <a> tags for github.com/owner/repo pattern
        github_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if _GITHUB_RE.match(href):
                # Exclude github.com/huggingface and similar org links
                parts = href.rstrip("/").split("/")
                if len(parts) >= 5:   # https://github.com/owner/repo
                    github_url = href.rstrip("/")
                    break

        return abstract, github_url

    except Exception as e:
        print(f"  [!] Failed to scrape HF paper page {paper_url}: {e}")
        return "", None


def fetch_top_paper() -> dict | None:
    """
    Scrape the #1 trending paper from huggingface.co/papers/trending.
    Returns a single article dict, or None if scraping fails.
    """
    try:
        resp = requests.get(HF_TRENDING_URL, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # HF renders paper links like /papers/2503.12345 — find the first one.
        # The <a> tag itself has no text; the title is in a parent <h3>.
        paper_link = None
        paper_title = None

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.match(r"^/papers/\d{4}\.\d+", href):
                paper_link = "https://huggingface.co" + href
                # Walk up ancestors to find the nearest <h3> title
                node = a.parent
                for _ in range(6):
                    if node is None:
                        break
                    h3 = node.find("h3")
                    if h3:
                        paper_title = h3.get_text(strip=True)
                        break
                    node = node.parent
                break

        if not paper_link:
            print("  [!] Could not find any paper links on HF trending page")
            return None

        # Fall back to fetching title from the paper page if not found in listing
        if not paper_title:
            paper_title = paper_link

        print(f"  Top HF paper: {paper_title}")
        abstract, github_url = _scrape_paper_page(paper_link)

        if github_url:
            print(f"  GitHub repo found: {github_url}")

        summary = abstract or paper_title
        now = datetime.now(timezone.utc).isoformat()

        return {
            "title":        paper_title,
            "url":          paper_link,
            "github_url":   github_url,
            "source":       "Trending Papers",
            "summary":      summary,
            "scraped":      summary,   # pre-populated — skip re-scraping
            "published_at": now,
            "is_github":    1,         # bypasses editorial filter
            "feed_mentions": 1,
        }

    except Exception as e:
        print(f"  [!] Failed to fetch HF trending papers: {e}")
        return None
