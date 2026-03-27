# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A daily AI newsletter system with two components that share a SQLite database:
- **`ai-newsletter-collector/`** — Python: fetches RSS feeds + GitHub trending, ranks with OpenAI, builds/sends email
- **`ai-newsletter-web/`** — TypeScript/Next.js: displays articles in a news feed UI
- **`data/articles.db`** — shared SQLite database (auto-created on first run)

## Commands

### Python Collector
```bash
cd ai-newsletter-collector
pip install -r requirements.txt   # first time only

python main.py                    # fetch news + rank with OpenAI
python email_builder.py           # build HTML email preview (saved to data/)
python email_builder.py --send    # build + send via Gmail
python run_daily.py --send        # full pipeline (main + email) — used by Task Scheduler
```

### Next.js Web App
```bash
cd ai-newsletter-web
npm install        # first time only
npm run dev        # http://localhost:3000
npm run build
npm start
```

## Architecture

### Data Flow
```
main.py
  → feeds.py (static list of (name, url, sector) tuples — edit to add/remove feeds)
  → rss.py (fetch + date-filter, 24-hour lookback)
  → categorizer.py (keyword → sector, fallback only)
  → ranker.py — per sector:
      1. scraper.py (parallel fetch of article URLs: og:title + og:description + body intro, ≤1000 chars each)
      2. LLM filter call (gpt-4o-mini): pick top 5 from candidates using scraped excerpts
      3. LLM summarize call (gpt-4o-mini): catchy ai_title + 150-200 word ai_summary for each selected
  → storage.py (INSERT OR IGNORE into articles.db)

email_builder.py
  → queries articles WHERE is_featured=1 AND date=today
  → renders inline-CSS HTML email
  → saves data/email_YYYY-MM-DD.html + optionally sends via Gmail SMTP

Next.js (npm run dev)
  → lib/db.ts reads articles.db directly via better-sqlite3 (server-side only)
  → page.tsx (revalidate=600, 10-min ISR) renders SectorSection per sector
  → featured articles (is_featured=1) → FeaturedCard grid
  → remaining articles → compact ArticleCard list
  → GET /api/articles?date=YYYY-MM-DD returns articles grouped by sector as JSON
```

### SQLite Schema (articles table)
| Column | Notes |
|---|---|
| `url` | UNIQUE — primary dedup key |
| `title` | Article headline |
| `source` | Feed name (e.g. "OpenAI Blog") |
| `sector` | `ai-updates` \| `ai-business` \| `ai-dev` |
| `summary` | Raw RSS excerpt (≤300 chars) |
| `ai_title` | LLM-generated catchy headline (≤12 words, not verbatim) |
| `ai_summary` | LLM-generated 150-200 word summary |
| `published_at` | ISO timestamp from RSS feed (may be null) |
| `fetched_at` | ISO timestamp when collector ran |
| `is_featured` | 1 = top 5 selected by OpenAI for this sector |
| `is_github` | 1 = from GitHub Trending scraper |
| `stars` | GitHub star count (null for RSS articles) |

Date filtering uses `DATE(COALESCE(published_at, fetched_at))`.

### Key Design Decisions
- **24-hour lookback** in `rss.py` — articles without a date are dropped; keeps only last 24h
- **60-candidate cap** in `ranker.py` — round-robin across sources before sending to OpenAI to avoid context limit errors and source bias
- **Title prefix dedup** in `storage.py` — first 60 chars of lowercase title checked against same-day articles (catches near-duplicates from different sources)
- **better-sqlite3 is a native module** — `next.config.js` externalizes it from webpack; must stay server-side only (never imported in client components)
- **DB migrations** in `storage.py` `init_db()` — ALTER TABLE statements wrapped in try/except to add new columns to existing databases without destroying data

### Environment Variables

**`ai-newsletter-collector/.env`**
```
DB_PATH=../data/articles.db
OPENAI_API_KEY=...
GMAIL_USER=...             # optional — only needed for email sending
GMAIL_APP_PASSWORD=...     # Gmail App Password (not account password)
EMAIL_TO=...
SPONSOR_NAME=...           # optional — enables sponsor block in email
SPONSOR_TEXT=...           # one-line sponsor pitch
SPONSOR_URL=...            # sponsor CTA link
```

**`ai-newsletter-web/.env.local`**
```
DB_PATH=../data/articles.db
```

Both paths are resolved relative to each repo's root directory.

### Windows Task Scheduler (7 AM daily)
- Program: `python.exe`
- Arguments: `run_daily.py --send`
- Start in: `ai-newsletter-collector/`
