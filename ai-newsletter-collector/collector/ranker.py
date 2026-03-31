"""
collector/ranker.py — AI-powered article ranking and summarisation pipeline.

Simplified pipeline (3-4 LLM calls total):
  1. Jaccard dedup          — remove duplicate stories by title word-overlap (free)
  2. Light scrape           — og:title + description + body intro for all articles
  3. LLM triage             — select top 12-15, score, categorize, classify tier
  4. Deep scrape            — full content for selected articles only
  5. LLM enrich top stories — overview, details, why_it_matters (with freshness check)
  6. LLM enrich quick hits  — one-liner summaries
  7. Diversity enforcement  — cap same-source and same-category
  8. Output validation

All tunable parameters live in config.py.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from openai import OpenAI

from config import (
    TRIAGE_MODEL, TRIAGE_TEMPERATURE,
    ENRICH_MODEL, ENRICH_TEMPERATURE,
    SUMMARIZE_MODEL, SUMMARIZE_TEMPERATURE,
    MAX_CANDIDATES,
    CROSS_SECTOR_THRESHOLD,
    TRIAGE_EXCERPT_CHARS, ENRICH_CONTENT_CHARS,
    FEED_MENTION_BOOST_CAP,
    MAX_ARTICLES_PER_SOURCE, MAX_ARTICLES_PER_CATEGORY,
    MAX_ARTICLES_PER_BONUS_CATEGORY,
    PUBLISH_MAX_ARTICLES,
    TOP_STORY_COUNT, QUICK_HIT_COUNT,
    OFFICIAL_SOURCES, NEWS_SOURCES,
    DEEP_SCRAPE_MAX_CHARS,
)
from collector.prompts import (
    TRIAGE_PROMPT,
    ENRICH_TOP_STORY_PROMPT, ENRICH_QUICK_HIT_PROMPT,
    CATEGORY_LIST, CATEGORY_DESCRIPTIONS,
)
from collector.scraper import ArticleScraper


# =============================================================================
# Title word extraction for Jaccard-based deduplication
# =============================================================================

_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "and", "or", "but", "nor",
    "with", "as", "by", "its", "it", "this", "that", "from", "into",
    "will", "can", "has", "have", "had", "may", "might", "would", "could",
    "not", "no", "all", "more", "over", "after", "about", "now", "just",
    "how", "why", "what", "who", "where", "when", "which",
    "says", "said", "gets", "got", "set", "put", "let", "hit",
    "launches", "launch", "released", "releases", "release",
    "announces", "announced", "announce", "reveals", "revealed", "reveal",
    "warns", "warned", "warn", "issues", "issued", "issue",
    "acquires", "acquired", "acquire", "buys", "bought", "buy",
    "raises", "raised", "raise", "funds", "funded", "fund",
    "cuts", "cut", "fires", "fired", "hire", "hires", "hired",
    "builds", "built", "build", "makes", "made", "make",
    "shows", "showed", "show", "beats", "beat", "tops", "top",
    "updates", "updated", "update", "adds", "added", "add",
    "blocks", "blocked", "block", "bans", "banned", "ban",
    "new", "latest", "major", "key", "big", "first", "next", "last",
    "million", "billion", "trillion", "percent", "year", "month", "week",
    "company", "startup", "firm", "team", "group", "deal", "round",
    "report", "reports", "study", "series", "funding",
    "use", "using", "used", "get",
})


def _title_words(title: str) -> set[str]:
    """Extract significant words from a title for Jaccard-based deduplication."""
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*", title)
    return {w.lower() for w in words if w.lower() not in _STOPWORDS and len(w) >= 3}


# =============================================================================
# Step 1 — Jaccard deduplication (free, no LLM)
# =============================================================================

def jaccard_dedup(articles: list[dict]) -> list[dict]:
    """
    Remove duplicate stories by title word-overlap (Jaccard similarity).
    When a duplicate pair is found, the later article is removed and its
    feed_mentions count is added to the survivor.
    """
    if len(articles) < 2:
        return articles

    word_sets = [_title_words(a["title"]) for a in articles]
    remove: set[int] = set()

    for i in range(len(articles)):
        if i in remove:
            continue
        ws_i = word_sets[i]
        if not ws_i:
            continue

        for j in range(i + 1, len(articles)):
            if j in remove:
                continue
            ws_j = word_sets[j]
            if not ws_j:
                continue

            union = ws_i | ws_j
            overlap = len(ws_i & ws_j) / len(union) if union else 0.0

            if overlap >= CROSS_SECTOR_THRESHOLD:
                articles[i]["feed_mentions"] = (
                    articles[i].get("feed_mentions", 1) + articles[j].get("feed_mentions", 1)
                )
                remove.add(j)

    if remove:
        print(f"  Jaccard dedup: removed {len(remove)} duplicate(s)")

    return [a for i, a in enumerate(articles) if i not in remove]


# =============================================================================
# Step 2 — Light scrape (all articles)
# =============================================================================

def scrape_all(articles: list[dict]) -> list[dict]:
    """Scrape all article pages in parallel using a single thread pool."""
    scraper = ArticleScraper()
    scraper.scrape_all(articles)
    scraped_count = sum(1 for a in articles if a.get("scraped"))
    print(f"  Scraped {scraped_count}/{len(articles)} successfully")
    return articles


# =============================================================================
# Step 3 — LLM Triage (single call: select + score + categorize + tier)
# =============================================================================

def llm_triage(articles: list[dict], client: OpenAI) -> list[dict]:
    """
    Single LLM call that selects the top 12-15 articles from the candidate pool,
    scoring, categorizing, and classifying tier in one pass.

    Replaces the old dedup + filter + summarize pipeline (3+ LLM calls).
    """
    # Round-robin sample so no source dominates
    candidates = _round_robin(articles, MAX_CANDIDATES)

    payload = [
        {
            "index":       i,
            "title":       a["title"],
            "source":      a["source"],
            "source_type": (
                "official" if a["source"] in OFFICIAL_SOURCES
                else "news" if a["source"] in NEWS_SOURCES
                else "secondary"
            ),
            "buzz":        a.get("feed_mentions", 1),
            "excerpt":     (a.get("scraped") or a.get("summary") or "")[:TRIAGE_EXCERPT_CHARS],
        }
        for i, a in enumerate(candidates)
    ]

    category_tags_str = "\n".join(f"- {c}" for c in CATEGORY_LIST)
    today = date.today().isoformat()

    prompt = TRIAGE_PROMPT.format(
        today_date=today,
        category_tags=category_tags_str,
        category_descriptions=CATEGORY_DESCRIPTIONS,
        articles=json.dumps(payload, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model=TRIAGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TRIAGE_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        valid_categories = set(CATEGORY_LIST)
        selected = []

        for item in data.get("selected", []):
            idx = item.get("index")
            if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
                continue

            article = candidates[idx]

            # Score
            raw_score = item.get("score")
            try:
                article["score"] = int(raw_score) if raw_score is not None else 5
            except (ValueError, TypeError):
                article["score"] = 5

            # Category
            cat = item.get("category", "")
            if article.get("is_github"):
                article["category"] = "Trending Repos & Papers"
            else:
                article["category"] = cat if cat in valid_categories else "AI Applications"
            article["sector"] = article["category"]

            # Story tier
            raw_tier = item.get("story_tier")
            try:
                article["story_tier"] = int(raw_tier) if raw_tier is not None else 0
            except (ValueError, TypeError):
                article["story_tier"] = 0

            # Primary source flag
            article["is_primary"] = bool(item.get("is_primary", True))

            # Reasoning (for debugging)
            article["triage_reason"] = item.get("reason", "")

            selected.append(article)

        # Apply buzz boost (only scoring adjustment we keep)
        for a in selected:
            mentions = a.get("feed_mentions", 1)
            buzz_boost = min(mentions - 1, FEED_MENTION_BOOST_CAP)
            a["score"] = a["score"] + buzz_boost

        print(f"  Triage: {len(selected)} selected from {len(candidates)} candidates")
        for a in selected:
            print(f"    [{a['score']:>2}] [tier={a.get('story_tier',0)}] "
                  f"{'P' if a.get('is_primary') else 'S'} | {a['title'][:60]}")

        return selected

    except Exception as exc:
        print(f"  [!] Triage failed: {exc} — using first 15 candidates as fallback")
        for a in candidates[:15]:
            a.setdefault("score", 5)
            a.setdefault("category", "AI Applications")
            a.setdefault("sector", "AI Applications")
            a.setdefault("story_tier", 0)
        return candidates[:15]


# =============================================================================
# Step 4 — Deep scrape (selected articles only)
# =============================================================================

def deep_scrape(articles: list[dict]) -> list[dict]:
    """Re-scrape selected articles with higher char limit for richer content."""
    scraper = ArticleScraper()
    scraper.deep_scrape_articles(articles, max_chars=DEEP_SCRAPE_MAX_CHARS)
    avg_len = sum(len(a.get("scraped", "")) for a in articles) // max(len(articles), 1)
    print(f"  Deep scrape: avg {avg_len} chars per article")
    return articles


# =============================================================================
# Step 5 — Diversity enforcement + per-category cap
# =============================================================================

def enforce_diversity_and_caps(articles: list[dict]) -> list[dict]:
    """
    Cap articles from same source and same category. Articles processed in
    score-descending order so highest-scored pieces are always retained.
    """
    _BONUS_CATEGORIES = {"Tutorials & Guides", "Trending Repos & Papers"}

    source_count: dict[str, int] = {}
    category_count: dict[str, int] = {}
    result: list[dict] = []
    dropped: list[tuple[dict, str]] = []

    for a in sorted(articles, key=lambda x: x.get("score") or 0, reverse=True):
        src = a.get("source", "")
        cat = a.get("category", "")
        cat_cap = MAX_ARTICLES_PER_BONUS_CATEGORY if cat in _BONUS_CATEGORIES else MAX_ARTICLES_PER_CATEGORY

        # Model releases always pass source cap
        is_model_release = cat == "Model Releases"

        if not is_model_release and source_count.get(src, 0) >= MAX_ARTICLES_PER_SOURCE:
            dropped.append((a, f"source cap ({src})"))
            continue
        if cat and category_count.get(cat, 0) >= cat_cap:
            dropped.append((a, f"category cap ({cat})"))
            continue

        source_count[src] = source_count.get(src, 0) + 1
        if cat:
            category_count[cat] = category_count.get(cat, 0) + 1
        result.append(a)

    if dropped:
        print(f"  [diversity-dropped] {len(dropped)} article(s):")
        for a, reason in dropped:
            print(f"    - {a.get('title', '')[:60]} | score={a.get('score')} | {reason}")

    return sorted(result, key=lambda x: x.get("score") or 0, reverse=True)


# =============================================================================
# Step 6 — Two-tier enrichment (top stories + quick hits)
# =============================================================================

def llm_enrich_top_stories(articles: list[dict], client: OpenAI) -> None:
    """
    Generate ai_title, ai_summary, key_points, and company_tag for top stories.
    Also performs freshness verification (is_stale flag).
    Uses deep-scraped content for richer extraction.
    Modifies articles in-place.
    """
    if not articles:
        return

    today = date.today().isoformat()

    payload = [
        {
            "index":   i,
            "title":   a["title"],
            "source":  a["source"],
            "content": (a.get("scraped") or a.get("summary") or "")[:ENRICH_CONTENT_CHARS],
        }
        for i, a in enumerate(articles)
    ]

    prompt = ENRICH_TOP_STORY_PROMPT.format(
        today_date=today,
        articles=json.dumps(payload, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model=ENRICH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=ENRICH_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        result_map = {
            int(r["index"]): r
            for r in data.get("articles", [])
            if "index" in r
        }

        for i, article in enumerate(articles):
            r = result_map.get(i, {})
            article["ai_title"]       = r.get("ai_title") or None
            article["ai_summary"]     = r.get("ai_summary") or ""
            # Map to DB-compatible fields
            article["overview"]       = article["ai_summary"]
            article["details"]        = json.dumps(r.get("key_points", []))
            article["why_it_matters"] = r.get("why_it_matters", "")
            article["company_tag"]    = r.get("company_tag", "")
            article["is_top_story"]   = 1
            article["is_stale"]       = r.get("is_stale", False)

    except Exception as exc:
        print(f"  [!] Top story enrichment failed: {exc}")
        for a in articles:
            a["is_top_story"] = 1
            a.setdefault("ai_title", None)
            a.setdefault("ai_summary", a.get("summary", ""))
            a.setdefault("overview", a.get("ai_summary", ""))
            a.setdefault("details", "[]")
            a.setdefault("why_it_matters", "")
            a.setdefault("company_tag", "")


def llm_enrich_quick_hits(articles: list[dict], client: OpenAI) -> None:
    """
    Generate ai_title, one_liner, and company_tag for quick hit articles.
    Modifies articles in-place.
    """
    if not articles:
        return

    payload = [
        {
            "index":   i,
            "title":   a["title"],
            "source":  a["source"],
            "content": (a.get("scraped") or a.get("summary") or "")[:ENRICH_CONTENT_CHARS],
        }
        for i, a in enumerate(articles)
    ]

    prompt = ENRICH_QUICK_HIT_PROMPT.format(
        articles=json.dumps(payload, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model=ENRICH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=ENRICH_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        result_map = {
            int(r["index"]): r
            for r in data.get("articles", [])
            if "index" in r
        }

        for i, article in enumerate(articles):
            r = result_map.get(i, {})
            article["ai_title"]    = r.get("ai_title") or None
            article["one_liner"]   = r.get("one_liner") or article.get("ai_summary", "")
            article["company_tag"] = r.get("company_tag", "")
            article["is_top_story"] = 0
            article["ai_summary"]  = article["one_liner"]

    except Exception as exc:
        print(f"  [!] Quick hit enrichment failed: {exc}")
        for a in articles:
            a["is_top_story"] = 0
            a.setdefault("ai_title", None)
            a.setdefault("one_liner", a.get("ai_summary", ""))
            a.setdefault("company_tag", "")


# =============================================================================
# Step 7 — Output validation
# =============================================================================

def _validate_articles(articles: list[dict]) -> None:
    """Post-process LLM output for quality control. Applies in-place."""
    for a in articles:
        title = a.get("ai_title") or ""
        if title:
            words = title.split()
            if len(words) > 12:
                a["ai_title"] = " ".join(words[:10])

        summary = a.get("ai_summary") or ""
        if len(summary.split()) < 15:
            fallback = a.get("scraped") or a.get("summary") or summary
            a["ai_summary"] = fallback[:500].strip() if fallback else None

        score = a.get("score")
        if score is not None:
            a["score"] = max(1, min(10, score))


# =============================================================================
# Helper
# =============================================================================

def _round_robin(articles: list[dict], limit: int) -> list[dict]:
    """Return up to `limit` articles sampled round-robin across sources."""
    by_source: dict[str, list[dict]] = {}
    for article in articles:
        by_source.setdefault(article["source"], []).append(article)

    result: list[dict] = []
    sources = list(by_source)
    i = 0
    while len(result) < limit and any(by_source[s] for s in sources):
        src = sources[i % len(sources)]
        if by_source[src]:
            result.append(by_source[src].pop(0))
        i += 1
    return result


# =============================================================================
# Public API — summarize_pinned (for GitHub/HF pinned articles)
# =============================================================================

def summarize_pinned(articles: list[dict]) -> list[dict]:
    """
    Run a lightweight summarise on pinned articles (GitHub repo + HF paper).
    These bypass the main pipeline entirely.
    """
    if not articles:
        return []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return articles
    client = OpenAI(api_key=api_key)

    # Use a simple summarize call for pinned articles
    payload = [
        {
            "index":          i,
            "original_title": a["title"],
            "source":         a["source"],
            "content":        (a.get("scraped") or a.get("summary") or "")[:1000],
        }
        for i, a in enumerate(articles)
    ]

    from collector.prompts import CATEGORY_LIST as _cats
    categories_str = ", ".join(f'"{c}"' for c in _cats)
    articles_json = json.dumps(payload, ensure_ascii=False)
    prompt = (
        f'For each article below, write:\n'
        f'- "title": punchy headline, 10 words or fewer\n'
        f'- "summary": 2-3 sentences (60-90 words)\n'
        f'- "category": one of [{categories_str}]\n'
        f'- "score": 1-10 editorial importance\n\n'
        f'Return strictly valid JSON, no prose, no markdown:\n'
        f'{{"articles": [{{"index": 0, "title": "...", "summary": "...", '
        f'"category": "...", "score": 5}}, ...]}}\n\n'
        f'Articles:\n{articles_json}'
    )

    try:
        response = client.chat.completions.create(
            model=SUMMARIZE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=SUMMARIZE_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        result_map = {int(r["index"]): r for r in data.get("articles", []) if "index" in r}

        valid_categories = set(_cats)
        for i, article in enumerate(articles):
            r = result_map.get(i, {})
            article["ai_title"]   = r.get("title") or None
            article["ai_summary"] = r.get("summary") or None
            cat = r.get("category", "")
            article["category"] = cat if cat in valid_categories else "Trending Repos & Papers"
            article["sector"]   = article["category"]
            raw_score = r.get("score")
            try:
                article["score"] = int(raw_score) if raw_score is not None else 5
            except (ValueError, TypeError):
                article["score"] = 5
    except Exception as exc:
        print(f"  [!] Pinned summarize failed: {exc}")
        for a in articles:
            a.setdefault("ai_title", None)
            a.setdefault("ai_summary", None)
            a.setdefault("category", "Trending Repos & Papers")
            a.setdefault("sector", "Trending Repos & Papers")
            a.setdefault("score", 5)

    for a in articles:
        a["category"]    = "Trending Repos & Papers"
        a["sector"]      = "Trending Repos & Papers"
        a["is_featured"] = 1
    return articles


# =============================================================================
# Public API — run_pipeline (called from main.py)
# =============================================================================

def run_pipeline(articles: list[dict]) -> list[dict]:
    """
    Simplified pipeline for regular articles.

    Steps:
      1. Jaccard dedup (free)
      2. Light scrape all articles
      3. LLM triage (single call: select + score + categorize + tier)
      4. Deep scrape selected articles (richer content for enrichment)
      5. Diversity enforcement
      6. LLM enrich top stories (with freshness verification)
      7. LLM enrich quick hits
      8. Handle stale demotions
      9. Output validation

    Returns only articles that passed all gates with is_featured=1.
    """
    if not articles:
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  [!] OPENAI_API_KEY not set — skipping AI ranking")
        for a in articles:
            a.update(is_featured=0, ai_title=None, ai_summary=None,
                     category=None, sector=None, score=None)
        return articles

    client = OpenAI(api_key=api_key)

    # Step 1: Jaccard dedup (free, no LLM)
    print(f"\nStep 1/7: Jaccard dedup ({len(articles)} articles)...")
    articles = jaccard_dedup(articles)

    # Step 2: Light scrape all articles
    print(f"Step 2/7: Scraping {len(articles)} article pages...")
    articles = scrape_all(articles)

    # Step 3: LLM triage (single call)
    print(f"Step 3/7: LLM triage ({len(articles)} candidates)...")
    articles = llm_triage(articles, client)

    # Step 4: Deep scrape selected articles for richer content
    print(f"Step 4/7: Deep scraping {len(articles)} selected articles...")
    articles = deep_scrape(articles)

    # Step 5: Diversity enforcement
    print("Step 5/7: Enforcing diversity and per-category caps...")
    articles = enforce_diversity_and_caps(articles)

    # Step 6+7: Two-tier enrichment
    # Sort by score descending, split into top stories + quick hits
    articles = sorted(articles, key=lambda x: x.get("score") or 0, reverse=True)
    top_stories = articles[:TOP_STORY_COUNT]
    quick_hits  = articles[TOP_STORY_COUNT : TOP_STORY_COUNT + QUICK_HIT_COUNT]

    print(f"Step 6/7: Enriching {len(top_stories)} top stories + {len(quick_hits)} quick hits...")
    llm_enrich_top_stories(top_stories, client)
    llm_enrich_quick_hits(quick_hits, client)

    # Handle stale demotions: if a top story is flagged as stale,
    # demote it to quick hits and promote the next candidate
    stale_stories = [a for a in top_stories if a.get("is_stale")]
    if stale_stories:
        print(f"  [!] {len(stale_stories)} stale story(ies) detected — demoting:")
        for a in stale_stories:
            print(f"    - {a.get('ai_title') or a.get('title', '')[:60]}")
            a["is_top_story"] = 0
            # Move stale story to quick hits
            top_stories.remove(a)
            quick_hits.append(a)

        # Promote next candidates from remaining pool if available
        remaining = [a for a in articles
                     if a not in top_stories and a not in quick_hits
                     and a.get("score", 0) >= 4]
        while len(top_stories) < TOP_STORY_COUNT and remaining:
            promoted = remaining.pop(0)
            # Quick enrich the promoted article as top story
            llm_enrich_top_stories([promoted], client)
            top_stories.append(promoted)

    # Recombine
    articles = top_stories + quick_hits

    print("Step 7/7: Validating output...")
    _validate_articles(articles)

    for a in articles:
        a["is_featured"] = 1

    print(f"\n  -> {len(articles)} articles ready to publish"
          f" ({len(top_stories)} top stories + {len(quick_hits)} quick hits)")
    return articles
