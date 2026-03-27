"""
test_scrape.py — Diagnostic tool to test RSS fetching and article scraping.

For every feed in feeds.py:
  1. Fetch the RSS feed and collect articles from the last 24 hours
  2. Scrape each article URL for og:title + og:description + body text
  3. Save everything to data/scrape_test_YYYY-MM-DD.json

Usage:
    python test_scrape.py             # fetch + scrape all feeds
    python test_scrape.py --no-scrape # RSS fetch only (faster, no article visits)
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from the collector package
sys.path.insert(0, str(Path(__file__).parent))

from feeds import FEEDS
from collector.rss import fetch_feed
from collector.scraper import scrape_all_parallel


def main():
    no_scrape = "--no-scrape" in sys.argv
    run_at = datetime.now(timezone.utc).isoformat()
    output_path = Path("data") / f"scrape_test_{run_at[:10]}.json"
    output_path.parent.mkdir(exist_ok=True)

    print(f"Testing {len(FEEDS)} feeds  |  scraping: {'OFF' if no_scrape else 'ON'}")
    print("=" * 60)

    results = []

    for name, url, sector in FEEDS:
        print(f"\n[{sector}] {name}")
        print(f"  URL: {url}")

        articles = fetch_feed(name, url, sector)
        print(f"  RSS articles found (last 24h): {len(articles)}")

        if not articles:
            results.append({
                "feed_name": name,
                "feed_url": url,
                "sector": sector,
                "status": "no_articles",
                "articles": [],
            })
            continue

        if not no_scrape:
            print(f"  Scraping {len(articles)} article pages...")
            scrape_all_parallel(articles)
            scraped_count = sum(1 for a in articles if a.get("scraped"))
            print(f"  Scraped successfully: {scraped_count}/{len(articles)}")
        else:
            for a in articles:
                a["scraped"] = None

        for a in articles:
            print(f"    • {a['title'][:80]}")

        results.append({
            "feed_name": name,
            "feed_url": url,
            "sector": sector,
            "status": "ok",
            "article_count": len(articles),
            "articles": [
                {
                    "title":        a["title"],
                    "url":          a["url"],
                    "published_at": a.get("published_at"),
                    "rss_summary":  a.get("summary", ""),
                    "scraped":      a.get("scraped", ""),
                }
                for a in articles
            ],
        })

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    total_articles = sum(r.get("article_count", 0) for r in results)
    failed_feeds   = [r["feed_name"] for r in results if r["status"] == "no_articles"]

    print(f"Total articles fetched : {total_articles}")
    print(f"Feeds with no articles : {len(failed_feeds)}")
    if failed_feeds:
        for name in failed_feeds:
            print(f"  [x] {name}")

    # ── Save output ────────────────────────────────────────────────────────────
    output = {
        "run_at": run_at,
        "feed_count": len(FEEDS),
        "total_articles": total_articles,
        "failed_feeds": failed_feeds,
        "feeds": results,
    }
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved -> {output_path}")


if __name__ == "__main__":
    main()
