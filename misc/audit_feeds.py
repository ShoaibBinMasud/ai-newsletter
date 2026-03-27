"""
audit_feeds.py — Test all feeds in feeds_v2.py for recency.

For each feed:
  - Fetch via feedparser (timeout 15s)
  - Find the most recent article date
  - Classify:
      ACTIVE  = at least one article in the last 30 days
      STALE   = feed works but newest article is older than 30 days
      DEAD    = HTTP error, parse failure, or empty feed

Outputs:
  data/feeds_audit.csv        — full results
  feeds_curated.py            — ACTIVE feeds only (ready to use as feeds.py)
"""

import csv
import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import requests

# Load feeds from feeds_v2.py
sys.path.insert(0, os.path.dirname(__file__))
from feeds_v2 import FEEDS

CUTOFF_DAYS = 30
TIMEOUT = 15
MAX_WORKERS = 20

os.makedirs("data", exist_ok=True)

def _parse_date(entry) -> datetime | None:
    """Try to extract a timezone-aware datetime from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # fallback: raw string fields
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass
    return None


def audit_feed(name: str, url: str, sector: str) -> dict:
    result = {
        "name": name,
        "url": url,
        "sector": sector,
        "status": "DEAD",
        "http_code": None,
        "total_entries": 0,
        "newest_article_date": None,
        "days_since_last": None,
        "note": "",
    }

    try:
        # First do a quick HTTP head to catch obvious failures
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FeedAudit/1.0)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        result["http_code"] = resp.status_code
        if resp.status_code >= 400:
            result["note"] = f"HTTP {resp.status_code}"
            return result

        # Parse with feedparser (using the already-fetched content to avoid double request)
        feed = feedparser.parse(resp.content, response_headers={"content-type": resp.headers.get("content-type", "")})

        if feed.bozo and not feed.entries:
            result["note"] = f"Parse error: {getattr(feed, 'bozo_exception', 'unknown')}"
            return result

        entries = feed.entries
        result["total_entries"] = len(entries)

        if not entries:
            result["note"] = "Empty feed (0 entries)"
            return result

        # Find the newest article date
        dates = []
        for entry in entries:
            d = _parse_date(entry)
            if d:
                # normalise to UTC
                if d.tzinfo is None:
                    d = d.replace(tzinfo=timezone.utc)
                else:
                    d = d.astimezone(timezone.utc)
                dates.append(d)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=CUTOFF_DAYS)

        if dates:
            newest = max(dates)
            result["newest_article_date"] = newest.strftime("%Y-%m-%d")
            delta = now - newest
            result["days_since_last"] = delta.days
            if newest >= cutoff:
                result["status"] = "ACTIVE"
            else:
                result["status"] = "STALE"
                result["note"] = f"Last article {delta.days} days ago"
        else:
            # Feed has entries but no parseable dates — assume active (conservative)
            result["status"] = "ACTIVE"
            result["note"] = "No parseable dates — assumed active"

    except requests.exceptions.Timeout:
        result["note"] = "Timeout"
    except requests.exceptions.SSLError as e:
        result["note"] = f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        result["note"] = f"Connection error: {e}"
    except Exception as e:
        result["note"] = f"Error: {e}"

    return result


def main():
    print(f"Auditing {len(FEEDS)} feeds (cutoff: last {CUTOFF_DAYS} days)...")
    print(f"Using {MAX_WORKERS} parallel workers. This may take a few minutes.\n")

    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(audit_feed, name, url, sector): (name, url, sector)
            for name, url, sector in FEEDS
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            status_icon = {"ACTIVE": "[+]", "STALE": "[~]", "DEAD": "[x]"}.get(result["status"], "[?]")
            print(f"  {status_icon} [{completed:3d}/{len(FEEDS)}] {result['status']:6s}  {result['name'][:50]:<50}  {result.get('note', '')}")

    # Sort: sector → status → name
    sector_order = {"ai-updates": 0, "ai-business": 1, "ai-dev": 2, "security": 3}
    status_order = {"ACTIVE": 0, "STALE": 1, "DEAD": 2}
    results.sort(key=lambda r: (
        sector_order.get(r["sector"], 9),
        status_order.get(r["status"], 9),
        r["name"].lower()
    ))

    # Summary
    active = [r for r in results if r["status"] == "ACTIVE"]
    stale  = [r for r in results if r["status"] == "STALE"]
    dead   = [r for r in results if r["status"] == "DEAD"]
    print(f"\n{'='*60}")
    print(f"  ACTIVE : {len(active):3d}  (updated in last {CUTOFF_DAYS} days)")
    print(f"  STALE  : {len(stale):3d}  (older than {CUTOFF_DAYS} days)")
    print(f"  DEAD   : {len(dead):3d}  (broken / unreachable)")
    print(f"{'='*60}\n")

    # Write CSV
    csv_path = "data/feeds_audit.csv"
    fieldnames = ["name", "url", "sector", "status", "http_code",
                  "total_entries", "newest_article_date", "days_since_last", "note"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"CSV saved: {csv_path}")

    # Deduplicate ACTIVE feeds by URL (keep first occurrence)
    seen_urls = set()
    unique_active = []
    for r in active:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_active.append(r)

    print(f"Unique ACTIVE feeds after dedup: {len(unique_active)}")

    # Write curated feeds file
    _write_curated(unique_active)


def _write_curated(active_results: list[dict]):
    """Generate feeds_curated.py with only active feeds."""
    by_sector = {}
    for r in active_results:
        by_sector.setdefault(r["sector"], []).append(r)

    sector_order = ["ai-updates", "ai-business", "ai-dev", "security"]
    sector_labels = {
        "ai-updates": "AI Updates: model releases, research, product launches",
        "ai-business": "AI Business: funding, M&A, enterprise, policy, markets",
        "ai-dev": "AI Dev: tools, libraries, SDKs, tutorials, infrastructure",
        "security": "Security: AI-driven threats, breaches, vulnerability research",
    }

    lines = [
        '"""',
        'feeds_curated.py — Auto-generated by audit_feeds.py',
        f'Generated: {datetime.now().strftime("%Y-%m-%d")}',
        f'Only feeds active in the last 30 days are included.',
        '"""',
        '',
        '# Each entry: (name, url, sector)',
        '# Sector values: "ai-updates" | "ai-business" | "ai-dev" | "security"',
        '',
        'FEEDS = [',
    ]

    for sector in sector_order:
        feeds = by_sector.get(sector, [])
        if not feeds:
            continue
        label = sector_labels.get(sector, sector)
        lines.append(f'    # \u2500\u2500 {label} {"─"*max(0, 72-len(label))}')
        for r in feeds:
            name_str = f'"{r["name"]}"'
            url_str  = f'"{r["url"]}"'
            sec_str  = f'"{r["sector"]}"'
            days = r.get("days_since_last")
            comment = f"  # {days}d ago" if days is not None else ""
            lines.append(f'    ({name_str:<48}, {url_str:<90}, {sec_str}),{comment}')
        lines.append('')

    lines.append(']')
    lines.append('')

    out_path = os.path.join(os.path.dirname(__file__), "feeds_curated.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))
    print(f"Curated feeds saved: {out_path}")
    print(f"  ({len(active_results)} feeds across {len(by_sector)} sectors)")


if __name__ == "__main__":
    main()
