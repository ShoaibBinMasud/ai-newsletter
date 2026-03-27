"""
collector/rss.py — RSS feed fetcher.

Parses individual feeds and returns articles whose publication date falls on
one of the edition's target dates. Articles without a parseable publication
date are dropped — we cannot verify whether they belong to this edition.

Date-based filtering (instead of a fixed lookback window) is more precise:
  - No timezone drift edge cases
  - No arbitrary hour buffers needed
  - Monday's coverage of Saturday + Sunday is explicit and easy to reason about

All parameters (per-feed cap, skip days, etc.) are read from config.py.
"""

import re
import html as html_lib
import feedparser
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from config import MAX_PER_FEED, NEWSLETTER_SKIP_DAYS, ARTICLE_FILTER_MODE, LOOKBACK_HOURS


# =============================================================================
# Edition date calculation
# =============================================================================

def get_edition_dates() -> frozenset[date]:
    """
    Return the set of calendar dates whose articles belong to today's edition.

    The newsletter skips certain days (configured via NEWSLETTER_SKIP_DAYS in
    config.py, default: Sunday). When today's run follows one or more skipped
    days, we extend coverage backwards to include all the missed dates.

    Examples (default: skip Sunday):
      Monday  → {Saturday, Sunday}   (2 dates — covers the skipped Sunday)
      Tuesday → {Monday}             (1 date)
      Saturday → {Friday}            (1 date)

    Returns a frozenset of date objects so callers can use fast `in` lookups.
    """
    # Use local time, not UTC. The newsletter is tied to the local calendar
    # day — the scheduled run happens at 7 AM local time, and "yesterday"
    # means yesterday in the user's timezone, not UTC.
    # Example: 9 PM EDT on Monday = 1 AM UTC Tuesday. UTC would wrongly
    # think it's Tuesday and collect Monday's articles instead of Sat+Sun.
    today    = datetime.now().date()
    lookback = today - timedelta(days=1)   # always start from yesterday
    dates: set[date] = {lookback}

    # Keep stepping back while the previous day was a skip day.
    # Example: Monday run → step back to Sunday (skip day) → add Saturday.
    while lookback.weekday() in NEWSLETTER_SKIP_DAYS:
        lookback -= timedelta(days=1)
        dates.add(lookback)

    return frozenset(dates)


# =============================================================================
# FeedFetcher class
# =============================================================================

class FeedFetcher:
    """
    Fetches and filters articles from a single RSS/Atom feed.

    Supports two filter modes (configured via ARTICLE_FILTER_MODE in config.py):
      "hours" — keep articles published within the last LOOKBACK_HOURS (default)
      "dates" — keep articles whose date matches the provided edition_dates

    Parameters
    ----------
    edition_dates : frozenset[date] | None
        Used in "dates" mode. Pass None (or omit) when using "hours" mode.
    cutoff_dt : datetime | None
        Used in "hours" mode. Pre-computed cutoff = now - LOOKBACK_HOURS.

    Example
    -------
        fetcher = FeedFetcher(cutoff_dt=datetime.now(timezone.utc) - timedelta(hours=12))
        articles = fetcher.fetch("OpenAI Blog", "https://...", "ai-updates")
    """

    def __init__(
        self,
        edition_dates: Optional[frozenset] = None,
        cutoff_dt: Optional[datetime] = None,
    ) -> None:
        self.edition_dates = edition_dates
        self.cutoff_dt     = cutoff_dt

    # -------------------------------------------------------------------------
    # Public method
    # -------------------------------------------------------------------------

    def fetch(self, name: str, url: str) -> list[dict]:
        """
        Fetch a single RSS/Atom feed and return articles published on the
        edition dates.

        Parameters
        ----------
        name : Human-readable feed name (e.g. "OpenAI Blog")
        url  : Feed URL

        Returns
        -------
        List of article dicts, each containing:
            title, url, source, summary, published_at,
            is_github, stars, feed_mentions
        """
        articles: list[dict] = []

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                link  = getattr(entry, "link",  "").strip()

                # Skip entries without a title or URL — nothing to show the reader.
                if not title or not link:
                    continue

                pub_dt = self._parse_date(entry)

                # Drop articles with no parseable date — we can't verify recency.
                if pub_dt is None:
                    continue

                # Apply the configured filter mode.
                if self.cutoff_dt is not None:
                    # Hours mode: keep articles published after the cutoff.
                    if pub_dt < self.cutoff_dt:
                        continue
                elif self.edition_dates is not None:
                    # Dates mode: keep articles whose calendar date is in the edition.
                    if pub_dt.date() not in self.edition_dates:
                        continue

                summary = self._clean_text(
                    getattr(entry, "summary", "") or getattr(entry, "description", ""),
                    max_chars=300,
                )

                articles.append({
                    "title":        title,
                    "url":          link,
                    "source":       name,
                    "summary":      summary,
                    "published_at": pub_dt.isoformat(),
                    "is_github":    0,
                    "stars":        None,
                    # feed_mentions starts at 1; incremented by dedup steps
                    # when duplicate copies of this story appear in other feeds.
                    "feed_mentions": 1,
                })

                # Cap at MAX_PER_FEED most-recent articles per feed.
                if len(articles) >= MAX_PER_FEED:
                    break

        except Exception as exc:
            print(f"  [!] Failed to fetch {name}: {exc}")

        return articles

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_date(entry) -> Optional[datetime]:
        """
        Extract a UTC-aware publication datetime from a feed entry.

        feedparser normalises dates into time.struct_time tuples stored as
        published_parsed or updated_parsed. Returns None if neither is present
        or parseable.
        """
        for attr in ("published_parsed", "updated_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    return datetime(*t[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
        return None

    @staticmethod
    def _clean_text(text: str, max_chars: int) -> str:
        """
        Sanitise raw RSS text:
          - Decode HTML entities  (&amp; → &, &#8217; → ')
          - Strip any remaining HTML tags
          - Collapse whitespace
          - Truncate to max_chars
        """
        text = html_lib.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]


# =============================================================================
# Module-level convenience wrapper  (used by main.py's thread pool)
# =============================================================================

def fetch_feed(name: str, url: str) -> list[dict]:
    """
    Convenience wrapper around FeedFetcher for use in a thread pool.

    Uses ARTICLE_FILTER_MODE from config.py:
      "hours" — filters by a rolling cutoff (now - LOOKBACK_HOURS)
      "dates" — filters by edition calendar dates (get_edition_dates())

    Called once per feed by the parallel fetcher in main.py.
    """
    if ARTICLE_FILTER_MODE == "hours":
        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
        return FeedFetcher(cutoff_dt=cutoff).fetch(name, url)
    else:
        return FeedFetcher(edition_dates=get_edition_dates()).fetch(name, url)
