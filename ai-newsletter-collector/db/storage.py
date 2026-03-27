"""SQLite storage — create schema, run migrations, and insert articles."""

import sqlite3
import os
from datetime import datetime, timezone
from config import ARTICLE_FILTER_MODE

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    url          TEXT    UNIQUE NOT NULL,
    source       TEXT,
    sector       TEXT,
    summary      TEXT,
    ai_title     TEXT,
    ai_summary   TEXT,
    published_at TEXT,
    fetched_at   TEXT,
    is_github    INTEGER DEFAULT 0,
    is_featured  INTEGER DEFAULT 0,
    stars        INTEGER,
    subcategory  TEXT,
    score        INTEGER,
    edition_date TEXT,   -- YYYY-MM-DD of the newsletter run that produced this article
    github_url   TEXT    -- GitHub repo link (HF papers only)
);
"""

# Migrations: add new columns to existing databases that were created before these columns existed
MIGRATIONS = [
    "ALTER TABLE articles ADD COLUMN ai_summary TEXT",
    "ALTER TABLE articles ADD COLUMN is_featured INTEGER DEFAULT 0",
    "ALTER TABLE articles ADD COLUMN ai_title TEXT",
    # Remove sources dropped from the pipeline (run once, safe to repeat)
    "DELETE FROM articles WHERE source IN ('arXiv cs.AI', 'arXiv cs.LG', 'Papers With Code')",
    "ALTER TABLE articles ADD COLUMN subcategory TEXT",
    "ALTER TABLE articles ADD COLUMN score INTEGER",
    # edition_date: the calendar date (YYYY-MM-DD) of the newsletter run.
    # Distinct from DATE(fetched_at) because Monday's run covers two days,
    # so articles published on Saturday correctly belong to the Monday edition.
    "ALTER TABLE articles ADD COLUMN edition_date TEXT",
    "ALTER TABLE articles ADD COLUMN github_url TEXT",
]


def get_db_path() -> str:
    """Read DB_PATH from .env (already loaded by main.py) or fall back to ./data/articles.db."""
    path = os.getenv("DB_PATH", "../data/articles.db")
    # Resolve relative to the collector root (one level up from db/)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(base, path)) if not os.path.isabs(path) else path


def init_db(db_path: str) -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure the schema exists."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_SQL)
    # Run migrations safely (ignore if column already exists)
    for migration in MIGRATIONS:
        try:
            conn.execute(migration)
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()
    return conn


def save_articles(conn: sqlite3.Connection, articles: list[dict]) -> int:
    """
    Insert articles, skipping exact URL duplicates (enforced by UNIQUE constraint).

    Deduplication is handled upstream in ranker.py:
      - pre_dedup_across_sectors() catches same-story articles across sectors (Jaccard)
      - _dedup_by_llm() clusters same-story articles within each sector (LLM)

    By the time articles reach save_articles(), they have already been deduplicated
    via LLM clustering + keyword matching. No further dedup is needed here.

    Returns the number of newly inserted rows.
    """
    fetched_at   = datetime.now(timezone.utc).isoformat()
    edition_date = fetched_at[:10]   # YYYY-MM-DD of this newsletter run
    inserted = 0

    for article in articles:
        # In "dates" mode: guard against future-dated or same-day articles
        # (articles are always from yesterday in that mode).
        # In "hours" mode: same-day articles are expected — skip this check.
        if ARTICLE_FILTER_MODE == "dates":
            pub_date = (article.get("published_at") or "")[:10]
            if pub_date and pub_date >= edition_date:
                print(f"  [skip] '{article.get('title', '')[:60]}' — published {pub_date} >= edition {edition_date}")
                continue

        try:
            conn.execute(
                """
                INSERT INTO articles
                    (title, url, source, sector, summary, ai_title, ai_summary,
                     published_at, fetched_at, is_github, is_featured, stars,
                     subcategory, score, edition_date, github_url)
                VALUES
                    (:title, :url, :source, :sector, :summary, :ai_title, :ai_summary,
                     :published_at, :fetched_at, :is_github, :is_featured, :stars,
                     :subcategory, :score, :edition_date, :github_url)
                ON CONFLICT(url) DO UPDATE SET
                    ai_title     = excluded.ai_title,
                    ai_summary   = excluded.ai_summary,
                    is_featured  = excluded.is_featured,
                    sector       = excluded.sector,
                    summary      = excluded.summary,
                    subcategory  = excluded.subcategory,
                    score        = excluded.score,
                    fetched_at   = excluded.fetched_at,
                    edition_date = excluded.edition_date,
                    github_url   = excluded.github_url
                """,
                {
                    "fetched_at":   fetched_at,
                    "edition_date": edition_date,
                    "ai_title":     article.get("ai_title"),
                    "ai_summary":   article.get("ai_summary"),
                    "is_featured":  article.get("is_featured", 0),
                    **{k: article.get(k) for k in
                       ("title", "url", "source", "sector", "summary",
                        "published_at", "is_github", "stars", "subcategory", "score",
                        "github_url")},
                },
            )
            if conn.execute("SELECT changes()").fetchone()[0]:
                inserted += 1
        except Exception as e:
            print(f"  [!] DB insert error for '{article.get('title', '')}': {e}")

    conn.commit()
    return inserted


def count_by_sector(conn: sqlite3.Connection) -> dict[str, int]:
    """Return a dict of sector → total article count."""
    rows = conn.execute(
        "SELECT sector, COUNT(*) FROM articles GROUP BY sector"
    ).fetchall()
    return {row[0]: row[1] for row in rows}
