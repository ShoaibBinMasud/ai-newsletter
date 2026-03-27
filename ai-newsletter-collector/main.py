"""
AI Newsletter — News Collector
-------------------------------
Fetches today's AI news, ranks the top articles with OpenAI,
and saves everything to the local SQLite database.

What's parallelised
-------------------
  1. RSS feed fetching  — all feeds are fetched concurrently
                          (FEED_FETCH_WORKERS threads, configured in config.py)
  2. Article scraping   — all article URLs scraped in parallel
                          (SCRAPE_WORKERS threads, inside ranker.py)

Usage
-----
    python main.py
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from feeds import FEEDS, WEB_SOURCES
from collector.rss import fetch_feed
from collector.web_feed import fetch_web_sources
from collector.github import fetch_trending
from collector.hf_papers import fetch_top_paper
from collector.ranker import run_pipeline, summarize_pinned
from db.storage import get_db_path, init_db, save_articles
from config import FEED_FETCH_WORKERS
from email_builder import build_html, save_preview, send_to_beehiiv


def _fetch_all_feeds() -> list[dict]:
    """
    Fetch all RSS feeds in parallel and return a flat list of articles.

    Uses FEED_FETCH_WORKERS concurrent threads (configured in config.py).
    Feeds that fail are silently skipped — a warning is printed by fetch_feed().

    Returns
    -------
    Flat list of article dicts (no sector assignment)
    """
    total     = len(FEEDS)
    completed = 0
    articles: list[dict] = []

    print(f"Fetching {total} RSS feeds ({FEED_FETCH_WORKERS} parallel workers)...")

    with ThreadPoolExecutor(max_workers=FEED_FETCH_WORKERS) as pool:
        futures = {
            pool.submit(fetch_feed, name, url): name
            for name, url in FEEDS
        }

        for future in as_completed(futures):
            name      = futures[future]
            completed += 1

            try:
                feed_articles = future.result()
            except Exception as exc:
                print(f"  [!] Error fetching {name}: {exc}")
                continue

            articles.extend(feed_articles)

            if feed_articles:
                print(f"  [{completed:>3}/{total}] {name}: {len(feed_articles)} articles")

    return articles


def main() -> None:
    db_path = get_db_path()
    print(f"Database: {db_path}\n")
    conn = init_db(db_path)

    # ── Step 1: Fetch all RSS feeds in parallel ──────────────────────────────
    articles = _fetch_all_feeds()
    print(f"\nRaw articles from RSS: {len(articles)}")

    # ── Step 1b: Scrape official blog pages (second layer, no RSS needed) ────
    print("\nScraping official blog pages...")
    web_articles = fetch_web_sources(WEB_SOURCES)
    articles.extend(web_articles)

    # ── Step 1c: Pinned articles — always 1 GitHub repo + 1 HF paper ─────────
    # These are handled COMPLETELY outside run_pipeline so they can never be lost.
    print("\nFetching top GitHub trending repo...")
    gh_repos = fetch_trending(limit=25)
    top_repo = sorted(gh_repos, key=lambda x: x.get("stars") or 0, reverse=True)[:1]

    print("Fetching top HuggingFace trending paper...")
    hf_paper = fetch_top_paper()
    pinned = top_repo + ([hf_paper] if hf_paper else [])
    print(f"  Pinned: {len(pinned)} article(s) — "
          + ", ".join(a.get("source", "") for a in pinned))

    print(f"Total raw articles (regular): {len(articles)}")

    # ── Step 2: Run the full pipeline on regular articles only ───────────────
    print("\nRunning global AI ranking pipeline...")
    all_articles = run_pipeline(articles)

    # ── Step 2b: Summarise pinned articles separately, then add ──────────────
    print("\nSummarising pinned articles...")
    pinned = summarize_pinned(pinned)
    all_articles = all_articles + pinned

    # ── Step 3: Save to database ─────────────────────────────────────────────
    print(f"\nSaving {len(all_articles)} articles to database...")
    inserted = save_articles(conn, all_articles)
    skipped  = len(all_articles) - inserted
    print(f"  ✓ {inserted} new articles saved  ({skipped} duplicates/skipped)")

    # ── Step 4: Build email + create Beehiiv draft ───────────────────────────
    edition_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Split featured articles into top stories and quick hits
    top_stories = [a for a in all_articles if a.get("is_top_story")]
    quick_hits  = [a for a in all_articles if a.get("is_featured") and not a.get("is_top_story")]

    featured_total = len(top_stories) + len(quick_hits)
    if featured_total > 0:
        print(f"\nBuilding email for {len(top_stories)} top stories + {len(quick_hits)} quick hits...")
        html         = build_html(top_stories, quick_hits, edition_date)
        preview_path = save_preview(html, edition_date)
        print(f"  ✓ Preview saved: {preview_path}")

        print("Creating Beehiiv draft...")
        send_to_beehiiv(html, edition_date)
    else:
        print("\n  [!] No featured articles — skipping email build")

    # ── Step 5: Print summary table ──────────────────────────────────────────
    print("\n─── Articles ───")
    if top_stories:
        print("  Top stories:")
        for a in top_stories:
            print(f"    • {a.get('ai_title') or a.get('title', '')[:60]}")
    if quick_hits:
        print("  Quick hits:")
        for a in quick_hits:
            print(f"    • {a.get('ai_title') or a.get('title', '')[:60]}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
