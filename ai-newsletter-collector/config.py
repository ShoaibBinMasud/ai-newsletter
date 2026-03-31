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
  7. Scoring
  8. Diversity Enforcement
  9. Source Tiers
  10. Newsletter Format
"""

# =============================================================================
# 1. LLM Models & Temperatures
# =============================================================================

TRIAGE_MODEL        = "gpt-4o"    # Triage: select + score + categorize
TRIAGE_TEMPERATURE  = 0.2         # Low for consistent selection, slight creativity

ENRICH_MODEL        = "gpt-4o"    # Enrichment: deep treatment of selected articles
ENRICH_TEMPERATURE  = 0.2         # Low enough to prevent hallucination

# Legacy aliases (kept for backward compatibility with summarize_pinned)
SUMMARIZE_MODEL       = ENRICH_MODEL
SUMMARIZE_TEMPERATURE = ENRICH_TEMPERATURE

# =============================================================================
# 2. Content Pipeline Thresholds
# =============================================================================

# Maximum articles taken into the pipeline (round-robin across sources).
MAX_CANDIDATES = 150

# Jaccard title-word overlap required to call two articles the "same story"
# during global pre-dedup (before scraping, fast path).
CROSS_SECTOR_THRESHOLD = 0.45

# Jaccard overlap for DB-level title dedup (runs at save time, after scoring).
STORAGE_DEDUP_THRESHOLD = 0.60

# Minimum number of articles triage should select (soft target).
TRIAGE_MIN_ARTICLES: int = 12

# Maximum articles in the final output.
PUBLISH_MAX_ARTICLES: int = 15

# =============================================================================
# 3. Scraper
# =============================================================================

SCRAPE_TIMEOUT = 8
SCRAPE_WORKERS = 12
SCRAPE_RETRIES = 1
SCRAPE_RETRY_DELAY = 3.0
MAX_BODY_CHARS = 1200
MAX_EXCERPT = 1500

# Deep scrape settings (for top story candidates after triage)
DEEP_SCRAPE_MAX_CHARS = 5000

# =============================================================================
# 4. RSS Feed Fetching
# =============================================================================

ARTICLE_FILTER_MODE: str = "hours"
LOOKBACK_HOURS:      int = 24

NEWSLETTER_SKIP_DAYS: frozenset[int] = frozenset({6})
MAX_PER_FEED = 15

# =============================================================================
# 5. Parallelism
# =============================================================================

FEED_FETCH_WORKERS = 20

# =============================================================================
# 6. Context Lengths Sent to LLM
# =============================================================================

# Triage gets short excerpts (enough to judge importance)
TRIAGE_EXCERPT_CHARS = 800

# Enrichment gets deep-scraped content (enough for numbers/benchmarks)
ENRICH_CONTENT_CHARS = 4000

# =============================================================================
# 7. Scoring
# =============================================================================

# Maximum score boost for appearing in multiple feeds.
# Formula: bonus = min(feed_mentions - 1, cap)
FEED_MENTION_BOOST_CAP = 2

# =============================================================================
# 8. Diversity Enforcement
# =============================================================================

MAX_ARTICLES_PER_SOURCE = 4
MAX_ARTICLES_PER_CATEGORY: int = 6
MAX_ARTICLES_PER_BONUS_CATEGORY: int = 3

# =============================================================================
# 9. Source Classification
# =============================================================================

# Same-day news sources — passed to LLM as source_type="news"
# These are NOT official company blogs, but they report breaking news same-day.
# Eligible for top stories when they cover news first or exclusively.
NEWS_SOURCES: frozenset[str] = frozenset({
    "TechCrunch (main)",
    "Reuters via Google News",
    "THE DECODER",
    "Hacker News Front Page",
    "InfoQ – AI, ML & Data Eng",
})

# Official source feeds — passed to LLM as source_type="official"
OFFICIAL_SOURCES: frozenset[str] = frozenset({
    # AI lab official blogs
    "OpenAI News", "Anthropic Blog", "Google DeepMind", "Google AI Blog",
    "Google Research", "Meta AI Blog", "Meta News", "Apple ML", "NVIDIA Blog",
    "Microsoft Research", "Amazon Science", "DeepMind Blog", "xAI Blog",
    "Mistral AI Blog", "Cohere Blog", "Perplexity Blog",
    # Tool/framework official blogs
    "Cursor Blog", "Windsurf Blog", "Hugging Face Blog", "LangChain",
    "Replicate Blog", "GitHub Blog", "Databricks Blog",
    # Academic research labs
    "Berkeley AI (BAIR)", "CMU ML Blog", "MIT AI News",
    # Cloud / infra primary sources
    "AWS News Blog - AI", "Google Cloud AI Blog", "Azure AI Blog",
    # Enterprise research
    "Salesforce Research", "Salesforce Blog", "IBM Research", "Adobe Research",
})

# =============================================================================
# 10. Newsletter Format (Rundown-style)
# =============================================================================

TOP_STORY_COUNT: int = 5
QUICK_HIT_COUNT: int = 15

OPENER_MODEL: str = "gpt-4o"
OPENER_TEMPERATURE: float = 0.4
