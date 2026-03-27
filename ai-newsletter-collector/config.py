"""
config.py — Central configuration for the AI Daily newsletter pipeline.

All tuneable parameters live here. Edit this file to experiment with the
pipeline without touching core logic. Restart the pipeline after any change.

Sections
--------
  1. LLM Models & Temperatures
  2. Content Pipeline Thresholds
  3. Scraper
  4. RSS Feed Fetching
  5. Parallelism
  6. Context Lengths Sent to LLM
  7. Scoring Bonuses
  8. Diversity Enforcement
  9. Source Tiers
"""

# =============================================================================
# 1. LLM Models & Temperatures
# =============================================================================

DEDUP_MODEL     = "gpt-4.1-mini"      # Clusters same-story articles
FILTER_MODEL    = "gpt-4.1-mini"      # Editorial selection
SUMMARIZE_MODEL = "gpt-4o" # Title / summary / score generation

DEDUP_TEMPERATURE     = 0.0   # Deterministic — clustering has a right answer
FILTER_TEMPERATURE    = 0.0   # Deterministic — editorial selection has a right answer
SUMMARIZE_TEMPERATURE = 0.2   # Low enough to prevent hallucinated facts, high enough for punchy titles

# =============================================================================
# 2. Content Pipeline Thresholds
# =============================================================================

# Maximum articles taken into the pipeline (round-robin across sources).
MAX_CANDIDATES = 150

# Maximum articles sent to the LLM dedup call per batch.
DEDUP_MAX_CANDIDATES = 60

# Maximum number of dedup rounds. Each round shuffles the pool and re-batches,
# so articles from different original batches get paired together.
# 3 rounds catches almost all semantic duplicates without excessive API cost.
DEDUP_MAX_ROUNDS: int = 3

# Minimum LLM-assigned score (1–10) for an article to be published.
PUBLISH_THRESHOLD = 6

# Ordered fallback thresholds tried when fewer than PUBLISH_MIN_ARTICLES pass.
PUBLISH_THRESHOLD_FALLBACKS: list[int] = [6, 5, 4]

# Minimum articles total before the threshold is lowered.
PUBLISH_MIN_ARTICLES: int = 5

# Hard cap on articles in the final output (applied after diversity enforcement).
PUBLISH_MAX_ARTICLES: int = 12

# Per-category hard cap on articles in the final output.
# Prevents any single topic from dominating the newsletter.
MAX_ARTICLES_PER_CATEGORY: int = 5

# Cap for bonus categories (Tutorials & Guides, GitHub & Open Source).
MAX_ARTICLES_PER_BONUS_CATEGORY: int = 2

# Jaccard title-word overlap required to call two articles the "same story"
# during global pre-dedup (before scraping, fast path).
CROSS_SECTOR_THRESHOLD = 0.45

# Jaccard overlap for DB-level title dedup (runs at save time, after scoring).
STORAGE_DEDUP_THRESHOLD = 0.60

# =============================================================================
# 3. Scraper
# =============================================================================

SCRAPE_TIMEOUT = 8
SCRAPE_WORKERS = 12
SCRAPE_RETRIES = 1
SCRAPE_RETRY_DELAY = 3.0
MAX_BODY_CHARS = 1200
MAX_EXCERPT = 1500

# =============================================================================
# 4. RSS Feed Fetching
# =============================================================================

# Article lookback filter mode:
#   "hours" (default) — keep articles published within the last LOOKBACK_HOURS.
#   "dates"           — keep articles whose calendar date matches edition dates.
ARTICLE_FILTER_MODE: str = "hours"   # "hours" | "dates"
LOOKBACK_HOURS:      int = 24        # used when ARTICLE_FILTER_MODE = "hours"

# Days of the week when NO newsletter is sent (Python weekday: 0=Mon, 6=Sun).
# Only relevant when ARTICLE_FILTER_MODE = "dates".
NEWSLETTER_SKIP_DAYS: frozenset[int] = frozenset({6})   # 6 = Sunday

# Maximum articles taken from a single RSS feed (most recent first).
MAX_PER_FEED = 15

# =============================================================================
# 5. Parallelism
# =============================================================================

# Parallel workers for fetching RSS feeds.
FEED_FETCH_WORKERS = 20

# Parallel HTTP workers for article scraping.
SCRAPE_WORKERS = 12

# =============================================================================
# 6. Context Lengths Sent to LLM
# =============================================================================

DEDUP_EXCERPT_CHARS = 400
FILTER_EXCERPT_CHARS = 800
SUMMARIZE_CONTENT_CHARS = 1000

# =============================================================================
# 7. Scoring Bonuses (applied after LLM scores, before PUBLISH_THRESHOLD gate)
# =============================================================================

# Maximum score boost awarded for appearing in multiple feeds.
# Formula: bonus = min(feed_mentions - 1, FEED_MENTION_BOOST_CAP)
FEED_MENTION_BOOST_CAP = 2

# Score bonus awarded to articles from tier-1 (official/primary) sources.
SOURCE_TIER1_BOOST = 1

# =============================================================================
# 8. Diversity Enforcement (applied after score gate)
# =============================================================================

# Maximum articles from the same source allowed in the final output.
MAX_ARTICLES_PER_SOURCE = 4

# Maximum articles sharing the same subcategory in the final output.
# (kept for DB backward compatibility — category cap is MAX_ARTICLES_PER_CATEGORY)
MAX_ARTICLES_PER_SUBCATEGORY = 3

# =============================================================================
# 9. Source Tiers
# =============================================================================
# Tier-1 sources receive a SOURCE_TIER1_BOOST score bonus.

TIER1_SOURCES: frozenset[str] = frozenset({
    # AI lab official blogs
    "OpenAI Blog",
    "Anthropic Blog",
    "Google DeepMind",
    "Google AI Blog",
    "Google Research",
    "Meta AI Blog",
    "Apple ML",
    "NVIDIA Blog",
    "Microsoft Research",
    "Amazon Science",
    "DeepMind Blog",
    "xAI Blog",
    "Mistral AI Blog",
    "Cohere Blog",
    "Perplexity Blog",
    # Academic research labs
    "Berkeley AI (BAIR)",
    "CMU ML Blog",
    "MIT AI News",
    # Cloud / infra primary sources
    "AWS News Blog - AI",
    "Google Cloud AI Blog",
    "Azure AI Blog",
})

# =============================================================================
# 10. Newsletter Format (Rundown-style)
# =============================================================================

# Number of deep stories with overview/details/why_it_matters
TOP_STORY_COUNT: int = 4

# Number of compact one-liner items in the quick hits section
QUICK_HIT_COUNT: int = 6

# Model and temperature for generating the editorial opener
OPENER_MODEL: str = "gpt-4o"
OPENER_TEMPERATURE: float = 0.4
