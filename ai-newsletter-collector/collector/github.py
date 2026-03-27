"""Scrape Trending Repos & Papers and fetch README excerpts for each repo."""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone


GITHUB_TRENDING_URL = "https://github.com/trending"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# How much README text to keep (chars) — enough for the LLM to understand the project
README_EXCERPT_CHARS = 800


def _fetch_readme(owner: str, repo: str) -> str:
    """
    Fetch the raw README from GitHub and return a truncated excerpt.
    Tries README.md first, then readme.md, then README (no extension).
    Returns empty string on any failure.
    """
    candidates = [
        f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
    ]
    for url in candidates:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=6)
            if resp.status_code == 200:
                text = resp.text.strip()
                # Strip markdown headers/badges for cleaner text
                lines = [
                    line for line in text.splitlines()
                    if not line.startswith("![") and not line.startswith("[![")
                ]
                clean = " ".join(" ".join(lines).split())
                return clean[:README_EXCERPT_CHARS]
        except Exception:
            continue
    return ""


def fetch_trending(limit: int = 25) -> list[dict]:
    """
    Scrape Trending Repos & Papers (daily) and return article dicts with README excerpts.
    README is pre-loaded into 'scraped' so the main scraper skips these URLs.
    """
    raw_repos: list[dict] = []

    try:
        response = requests.get(GITHUB_TRENDING_URL, headers=_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for item in soup.select("article.Box-row")[:limit]:
            h2 = item.select_one("h2 a")
            if not h2:
                continue

            href = h2.get("href", "").strip("/")
            if not href or href.count("/") != 1:
                continue

            owner, repo_name = href.split("/", 1)
            full_name = f"{owner}/{repo_name}"
            url = f"https://github.com/{full_name}"

            description_el = item.select_one("p")
            description = description_el.get_text(strip=True) if description_el else ""

            stars_el = item.select("a.Link--muted")
            total_stars = 0
            for a in stars_el:
                text = a.get_text(strip=True).replace(",", "")
                if text.isdigit():
                    total_stars = int(text)
                    break

            raw_repos.append({
                "owner":       owner,
                "repo_name":   repo_name,
                "full_name":   full_name,
                "url":         url,
                "description": description,
                "stars":       total_stars if total_stars else None,
            })

    except Exception as e:
        print(f"  [!] Failed to fetch Trending Repos & Papers: {e}")
        return []

    if not raw_repos:
        return []

    # Fetch READMEs in parallel — each is a quick raw text request
    print(f"  Fetching READMEs for {len(raw_repos)} trending repos...")
    readmes: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(_fetch_readme, r["owner"], r["repo_name"]): r["full_name"]
            for r in raw_repos
        }
        for future in as_completed(futures):
            full_name = futures[future]
            readmes[full_name] = future.result()

    fetched = sum(1 for v in readmes.values() if v)
    print(f"  READMEs fetched: {fetched}/{len(raw_repos)}")

    articles: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    for r in raw_repos:
        readme = readmes.get(r["full_name"], "")
        # Build a rich summary: description + README excerpt
        summary_parts = [p for p in [r["description"], readme] if p]
        summary = " | ".join(summary_parts) if summary_parts else ""

        title = f"{r['full_name']}"
        if r["description"]:
            title = f"{r['full_name']} — {r['description'][:80]}"

        articles.append({
            "title":        title,
            "url":          r["url"],
            "source":       "Trending Repos & Papers",
            "summary":      summary,
            "scraped":      summary,   # pre-populated — scraper will skip this URL
            "published_at": now,
            "is_github":    1,
            "stars":        r["stars"],
            "feed_mentions": 1,
        })

    return articles
