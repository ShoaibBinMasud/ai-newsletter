"""
collector/ranker.py — AI-powered article ranking and summarisation pipeline.

Single global pool pipeline:
  1. Global Jaccard dedup       remove duplicate stories by title word-overlap
  2. Global LLM dedup           cluster same-story articles, keep richest, track mentions
  3. Parallel scraping          og:title + description + body intro (≤ MAX_EXCERPT chars)
  4. LLM editorial filter       select top ~30-45 genuinely important stories
  5. LLM summarise + categorise title, summary, category (9-topic taxonomy), score
  6. Score bonuses              feed_mentions count + source tier + category priority
  7. Score gate                 discard articles below PUBLISH_THRESHOLD
  8. Diversity enforcement      cap same-source and same-category articles
  9. Output validation          clamp scores, truncate overlong titles

All tunable parameters (model names, temperatures, thresholds, etc.) live in config.py.
"""

import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

from config import (
    DEDUP_MODEL,      FILTER_MODEL,      SUMMARIZE_MODEL,
    DEDUP_TEMPERATURE, FILTER_TEMPERATURE, SUMMARIZE_TEMPERATURE,
    MAX_CANDIDATES,   DEDUP_MAX_CANDIDATES, DEDUP_MAX_ROUNDS, PUBLISH_THRESHOLD,
    PUBLISH_THRESHOLD_FALLBACKS, PUBLISH_MIN_ARTICLES, PUBLISH_MAX_ARTICLES,
    CROSS_SECTOR_THRESHOLD,
    DEDUP_EXCERPT_CHARS, FILTER_EXCERPT_CHARS, SUMMARIZE_CONTENT_CHARS,
    FEED_MENTION_BOOST_CAP, SOURCE_TIER1_BOOST, TIER1_SOURCES,
    MAX_ARTICLES_PER_SOURCE, MAX_ARTICLES_PER_SUBCATEGORY,
    MAX_ARTICLES_PER_CATEGORY, MAX_ARTICLES_PER_BONUS_CATEGORY,
    SCRAPE_WORKERS,
)
from collector.prompts import (
    DEDUP_PROMPT, FILTER_PROMPT, SUMMARIZE_PROMPT,
    CATEGORY_LIST, CATEGORY_DESCRIPTIONS,
)
from collector.scraper import ArticleScraper


# =============================================================================
# Title word extraction for Jaccard-based deduplication
# =============================================================================

_STOPWORDS: frozenset[str] = frozenset({
    # Grammar / function words
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "and", "or", "but", "nor",
    "with", "as", "by", "its", "it", "this", "that", "from", "into",
    "will", "can", "has", "have", "had", "may", "might", "would", "could",
    "not", "no", "all", "more", "over", "after", "about", "now", "just",
    "how", "why", "what", "who", "where", "when", "which",
    # Generic action verbs
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
    # Generic qualifiers / size words
    "new", "latest", "major", "key", "big", "first", "next", "last",
    "million", "billion", "trillion", "percent", "year", "month", "week",
    # Generic company/deal nouns
    "company", "startup", "firm", "team", "group", "deal", "round",
    "report", "reports", "study", "series", "funding",
    # Generic verbs
    "use", "using", "used", "get",
})


def _title_words(title: str) -> set[str]:
    """Extract significant words from a title for Jaccard-based deduplication."""
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*", title)
    return {w.lower() for w in words if w.lower() not in _STOPWORDS and len(w) >= 3}


# =============================================================================
# Step 1 — Global Jaccard deduplication
# =============================================================================

def global_jaccard_dedup(articles: list[dict]) -> list[dict]:
    """
    Remove duplicate stories across the entire article pool using title
    word-overlap (Jaccard similarity).

    This runs before any scraping or LLM calls, so it's cheap and fast.
    When a duplicate pair is found:
      - The later article (higher index) is removed.
      - Its feed_mentions count is added to the survivor.

    Parameters
    ----------
    articles : flat list of all raw article dicts

    Returns
    -------
    Deduplicated list with feed_mentions accumulated.
    """
    if len(articles) < 2:
        return articles

    word_sets: list[set[str]] = [_title_words(a["title"]) for a in articles]
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

            union   = ws_i | ws_j
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
# Step 2 — Global LLM deduplication
# =============================================================================

def global_llm_dedup(articles: list[dict], client: OpenAI) -> list[dict]:
    """
    Multi-round convergent LLM deduplication.

    How it works
    ------------
    Each round shuffles the pool, then splits into batches of DEDUP_MAX_CANDIDATES
    and deduplicates each batch. Shuffling is critical: it breaks the original
    batch boundaries so articles that were in different batches last round get
    paired together this round.

    Example — LiteLLM pair (share only 1 title word, needs LLM to match):
      "LiteLLM Hacked, Malware Targets Kubernetes Clusters"
      "LiteLLM Backdoored via Trivy CI/CD Compromise"
      Round 1: both in different batches → missed
      Round 2: shuffle → now in same batch → caught ✓

    Convergence
    -----------
    Rounds continue until the pool fits in a single batch (final pass) or
    no articles were removed in a round (converged). Capped at DEDUP_MAX_ROUNDS
    to keep runtime predictable.

    Survivors carry accumulated feed_mentions so the "buzz" signal is preserved.
    """
    if len(articles) <= 1:
        return articles

    original_count = len(articles)

    for round_num in range(1, DEDUP_MAX_ROUNDS + 1):
        before = len(articles)

        if len(articles) <= DEDUP_MAX_CANDIDATES:
            # Small enough for a single call — final definitive pass
            articles = _dedup_batch(articles, client)
            print(f"  LLM dedup round {round_num} (final): {before} → {len(articles)}")
            break

        # Shuffle before each round to mix articles across original batch boundaries
        random.shuffle(articles)

        result: list[dict] = []
        for i in range(0, len(articles), DEDUP_MAX_CANDIDATES):
            result.extend(_dedup_batch(articles[i : i + DEDUP_MAX_CANDIDATES], client))
        articles = result

        removed_this_round = before - len(articles)
        print(f"  LLM dedup round {round_num}: {before} → {len(articles)}"
              + (f" (-{removed_this_round})" if removed_this_round else " (no change)"))

        if removed_this_round == 0:
            # Pool has converged — no point running more rounds
            break

    total_removed = original_count - len(articles)
    print(f"  LLM dedup total: {original_count} → {len(articles)} ({total_removed} removed)")
    return articles


def _dedup_batch(articles: list[dict], client: OpenAI, *, skip_irrelevant: bool = False) -> list[dict]:
    """Run LLM dedup on a single batch of articles. Returns deduplicated list.

    Parameters
    ----------
    skip_irrelevant : bool
        If True, ignore the LLM's "irrelevant" list — useful for the final
        dedup pass where articles have already been vetted by the filter.
    """
    if len(articles) <= 1:
        return articles

    payload = [
        {
            "index":   i,
            "title":   a["title"],
            "source":  a["source"],
            "excerpt": (a.get("scraped") or a.get("summary") or "")[:DEDUP_EXCERPT_CHARS],
        }
        for i, a in enumerate(articles)
    ]

    prompt = DEDUP_PROMPT.format(articles=json.dumps(payload, ensure_ascii=False))

    try:
        response = client.chat.completions.create(
            model=DEDUP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=DEDUP_TEMPERATURE,
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        data     = json.loads(response.choices[0].message.content)
        clusters = data.get("clusters", [])

        # Collect irrelevant indices (lenient gate — obvious non-AI noise only)
        # Skip this entirely for the post-filter pass — those articles were already approved.
        if skip_irrelevant:
            irrelevant: set[int] = set()
        else:
            irrelevant = {
                i for i in data.get("irrelevant", [])
                if isinstance(i, int) and 0 <= i < len(articles)
            }
            if irrelevant:
                print(f"  [dedup] pre-filter dropped {len(irrelevant)} irrelevant article(s)")

        seen: set[int] = set()
        valid_clusters: list[list[int]] = []

        for cluster in clusters:
            valid = [
                i for i in cluster
                if isinstance(i, int) and 0 <= i < len(articles)
                and i not in seen and i not in irrelevant
            ]
            if valid:
                valid_clusters.append(valid)
                seen.update(valid)

        for i in range(len(articles)):
            if i not in seen and i not in irrelevant:
                valid_clusters.append([i])

        kept: list[dict] = []
        for cluster in valid_clusters:
            best_idx = max(
                cluster,
                key=lambda idx: len(articles[idx].get("scraped") or articles[idx].get("summary") or "")
            )
            survivor = articles[best_idx]
            survivor["feed_mentions"] = sum(
                articles[idx].get("feed_mentions", 1) for idx in cluster
            )
            kept.append(survivor)

        return kept

    except Exception as exc:
        print(f"  [!] LLM dedup batch failed, skipping: {exc}")
        return articles


# =============================================================================
# Step 3 — Parallel scraping
# =============================================================================

def scrape_all(articles: list[dict]) -> list[dict]:
    """Scrape all article pages in parallel using a single thread pool."""
    scraper = ArticleScraper()
    scraper.scrape_all(articles)
    scraped_count = sum(1 for a in articles if a.get("scraped"))
    print(f"  Scraped {scraped_count}/{len(articles)} successfully")
    return articles


# =============================================================================
# Step 4 — LLM editorial filter
# =============================================================================

def llm_filter(articles: list[dict], client: OpenAI) -> list[dict]:
    """
    Single LLM call that selects the top ~30-45 most important AI stories
    from the full candidate pool.

    Returns only the selected articles.
    """
    # Round-robin sample so no source dominates
    candidates = _round_robin(articles, MAX_CANDIDATES)

    payload = [
        {
            "index":   i,
            "title":   a["title"],
            "source":  a["source"],
            "buzz":    a.get("feed_mentions", 1),
            "excerpt": (a.get("scraped") or a.get("summary") or "")[:FILTER_EXCERPT_CHARS],
        }
        for i, a in enumerate(candidates)
    ]

    category_tags_str = "\n".join(f"- {c}" for c in CATEGORY_LIST)
    prompt = FILTER_PROMPT.format(
        category_tags=category_tags_str,
        articles=json.dumps(payload, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model=FILTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=FILTER_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        def _to_valid_indices(key: str) -> list[int]:
            return [
                int(v) for v in data.get(key, [])
                if isinstance(v, (int, float)) and 0 <= int(v) < len(candidates)
            ]

        relevant_idx = _to_valid_indices("relevant")
        selected_idx = _to_valid_indices("selected")

        selected_set = set(selected_idx)
        dropped = [candidates[i] for i in range(len(candidates)) if i not in selected_set]
        print(f"  Filter: {len(relevant_idx)} relevant → {len(selected_idx)} selected"
              f" ({len(dropped)} dropped)")
        print(f"  [filter-kept]    " + " | ".join(candidates[i]["title"][:60] for i in selected_idx))
        print(f"  [filter-dropped] " + " | ".join(a["title"][:60] for a in dropped))

        selected = [candidates[i] for i in selected_idx]
        return selected

    except Exception as exc:
        print(f"  [!] Filter failed: {exc} — using first 30 candidates as fallback")
        return candidates[:30]


# =============================================================================
# Step 5 — LLM summarise + categorise
# =============================================================================

def llm_summarize_and_categorize(articles: list[dict], client: OpenAI) -> list[dict]:
    """
    Generate ai_title, ai_summary, category, and score for each article.

    Processes in batches of 20 to keep payloads manageable.
    Category is validated against CATEGORY_LIST; invalid values fall back
    to "AI Applications".
    """
    if not articles:
        return articles

    category_tags_str = "\n".join(f"- {c}" for c in CATEGORY_LIST)
    valid_categories  = set(CATEGORY_LIST)

    # Process in batches of 20
    batch_size = 20
    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start : batch_start + batch_size]
        _summarize_batch(batch, client, category_tags_str, valid_categories)

    return articles


def _summarize_batch(
    articles: list[dict],
    client: OpenAI,
    category_tags_str: str,
    valid_categories: set[str],
) -> None:
    """Summarize and categorize a single batch. Modifies articles in-place."""
    if not articles:
        return

    payload = [
        {
            "index":          i,
            "original_title": a["title"],
            "source":         a["source"],
            "buzz":           a.get("feed_mentions", 1),
            "content":        (a.get("scraped") or a.get("summary") or "")[:SUMMARIZE_CONTENT_CHARS],
        }
        for i, a in enumerate(articles)
    ]

    from datetime import date
    prompt = SUMMARIZE_PROMPT.format(
        today_date=date.today().isoformat(),
        category_tags=category_tags_str,
        category_descriptions=CATEGORY_DESCRIPTIONS,
        articles=json.dumps(payload, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model=SUMMARIZE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=SUMMARIZE_TEMPERATURE,
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

            article["ai_title"]   = r.get("title")   or None
            article["ai_summary"] = r.get("summary") or None

            # Trending Repos & Papers repos always get their own category — don't let
            # the LLM assign them to "Research & Open Source" or similar.
            if article.get("is_github"):
                article["category"] = "Trending Repos & Papers"
            else:
                cat = r.get("category") or None
                article["category"] = cat if cat in valid_categories else "AI Applications"
            # Store in sector column for DB compatibility
            article["sector"] = article["category"]

            raw_score = r.get("score")
            try:
                article["score"] = int(raw_score) if raw_score is not None else None
            except (ValueError, TypeError):
                article["score"] = None

    except Exception as exc:
        print(f"  [!] Summarize batch failed: {exc}")
        for a in articles:
            a.setdefault("ai_title",   None)
            a.setdefault("ai_summary", None)
            default_cat = "Trending Repos & Papers" if a.get("is_github") else "AI Applications"
            a.setdefault("category",   default_cat)
            a.setdefault("sector",     default_cat)
            a.setdefault("score",       None)


# =============================================================================
# Step 6 — Score bonuses
# =============================================================================

# Categories that get a +1 priority bonus (top of the newsletter)
_HIGH_PRIORITY_CATEGORIES = frozenset({
    "Model Releases",
    "Products & Features",
    "RAG, Agents & Techniques",
})

def apply_score_bonuses(articles: list[dict]) -> list[dict]:
    """
    Adjust LLM-assigned scores based on signals the LLM can't see:

    Feed mention bonus
      An article that appeared in 3 independent feeds is more newsworthy
      than one from a single source. Bonus = min(feed_mentions - 1, cap).

    Source tier bonus
      Official blogs (OpenAI, Anthropic, Google Research, etc.) are primary
      sources. TIER1_SOURCES defined in config.py.

    Category priority bonus
      High-priority categories (Model Releases, Products & Features,
      RAG/Agents/Techniques) get +1 to ensure they surface above generic news.

    All scores are clamped to [1, 10] in _validate_articles (Step 9).
    """
    for a in articles:
        score = a.get("score")
        if score is None:
            continue

        mentions      = a.get("feed_mentions", 1)
        mention_bonus = min(mentions - 1, FEED_MENTION_BOOST_CAP)

        tier_bonus = SOURCE_TIER1_BOOST if a.get("source") in TIER1_SOURCES else 0

        category_bonus = 1 if a.get("category") in _HIGH_PRIORITY_CATEGORIES else 0

        a["score"] = score + mention_bonus + tier_bonus + category_bonus

    return articles


# =============================================================================
# Step 7 — Dynamic score gate
# =============================================================================

def apply_score_gate(articles: list[dict]) -> list[dict]:
    """
    Apply a waterfall of score thresholds until we reach PUBLISH_MIN_ARTICLES
    total across the pool. Returns articles passing the threshold.
    Model Releases and pinned articles always pass regardless of score.
    """
    all_thresholds = [PUBLISH_THRESHOLD] + list(PUBLISH_THRESHOLD_FALLBACKS)

    # Model Releases always pass — these are high-signal by definition
    _ALWAYS_PASS_CATEGORIES = {"Model Releases"}

    for threshold in all_thresholds:
        candidates = [
            a for a in articles
            if (a.get("score") or 0) >= threshold
            or a.get("category") in _ALWAYS_PASS_CATEGORIES
        ]
        if len(candidates) >= PUBLISH_MIN_ARTICLES:
            dropped = [a for a in articles if a not in candidates]
            suffix = f" (lowered from {PUBLISH_THRESHOLD})" if threshold < PUBLISH_THRESHOLD else ""
            print(f"  Score gate: {len(candidates)}/{len(articles)} scored ≥{threshold}{suffix}")
            if dropped:
                print(f"  [score-dropped] " + " | ".join(
                    f"{a.get('title', '')[:50]} (score={a.get('score')}, cat={a.get('category', '?')})"
                    for a in dropped
                ))
            return candidates

    lowest = all_thresholds[-1]
    result = [
        a for a in articles
        if (a.get("score") or 0) >= lowest
        or a.get("category") in _ALWAYS_PASS_CATEGORIES
    ]
    dropped = [a for a in articles if a not in result]
    print(f"  Score gate: {len(result)}/{len(articles)} scored ≥{lowest} (lowest fallback)")
    if dropped:
        print(f"  [score-dropped] " + " | ".join(
            f"{a.get('title', '')[:50]} (score={a.get('score')}, cat={a.get('category', '?')})"
            for a in dropped
        ))
    return result


# =============================================================================
# Step 8 — Diversity enforcement + per-category cap
# =============================================================================

def enforce_diversity_and_caps(articles: list[dict]) -> list[dict]:
    """
    Cap the number of articles from the same source and same category
    in the final published list to ensure variety for the reader.

    Articles are processed in score-descending order so the highest-scored
    pieces are always retained when a cap is reached.

    Caps (configured in config.py):
      MAX_ARTICLES_PER_SOURCE        — prevents source dominance
      MAX_ARTICLES_PER_CATEGORY      — per-category cap for balance
      MAX_ARTICLES_PER_BONUS_CATEGORY — lower cap for Tutorials & GitHub categories
    """
    _BONUS_CATEGORIES = {"Tutorials & Guides", "Trending Repos & Papers"}

    source_count:   dict[str, int] = {}
    category_count: dict[str, int] = {}
    result: list[dict] = []
    dropped: list[tuple[dict, str]] = []

    for a in sorted(articles, key=lambda x: x.get("score") or 0, reverse=True):
        src = a.get("source", "")
        cat = a.get("category", "")
        cat_cap = MAX_ARTICLES_PER_BONUS_CATEGORY if cat in _BONUS_CATEGORIES else MAX_ARTICLES_PER_CATEGORY

        # Model releases from any source always pass — never let source cap bury a launch
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
# Step 9 — Output validation
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
# Module-level helper
# =============================================================================

def _round_robin(articles: list[dict], limit: int) -> list[dict]:
    """
    Return up to `limit` articles sampled round-robin across sources.

    Prevents a single prolific source from filling the entire candidate pool.
    """
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
# Public API  (called from main.py)
# =============================================================================

def summarize_pinned(articles: list[dict]) -> list[dict]:
    """
    Run only the summarise + categorise step on pinned articles (GitHub repo + HF paper).
    Forces category to 'Trending Repos & Papers' and sets is_featured=1.
    Called from main.py after run_pipeline().
    """
    if not articles:
        return []
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return articles
    client = OpenAI(api_key=api_key)
    llm_summarize_and_categorize(articles, client)
    for a in articles:
        a["category"]    = "Trending Repos & Papers"
        a["sector"]      = "Trending Repos & Papers"
        a["is_featured"] = 1
    return articles


def run_pipeline(articles: list[dict]) -> list[dict]:
    """
    Full global pool pipeline for regular articles. Pinned articles
    (GitHub trending repo + HF paper) are handled separately in main.py
    via summarize_pinned() and never passed here.

    Steps:
      1. Global Jaccard dedup
      2. Global LLM dedup (batched)
      3. Scrape all articles in parallel
      4. LLM editorial filter (global, picks top ~30-45)
      5. Final dedup pass on filtered set
      6. LLM summarise + categorise
      7. Score bonuses
      8. Score gate
      9. Diversity enforcement + per-category cap

    Returns only articles that passed all gates with is_featured=1.
    """
    # Seed RNG with today's date so repeated runs on the same day produce
    # the same shuffle order in global_llm_dedup, giving consistent results.
    from datetime import date
    random.seed(date.today().isoformat())

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

    print(f"\nStep 1/9: Jaccard dedup ({len(articles)} articles)...")
    articles = global_jaccard_dedup(articles)

    print(f"Step 2/9: LLM dedup ({len(articles)} articles)...")
    articles = global_llm_dedup(articles, client)

    print(f"Step 3/9: Scraping {len(articles)} article pages...")
    articles = scrape_all(articles)

    print(f"Step 4/9: LLM filter ({len(articles)} candidates)...")
    articles = llm_filter(articles, client)

    print(f"  Final dedup pass on {len(articles)} filtered articles...")
    articles = _dedup_batch(articles, client, skip_irrelevant=True)

    print(f"Step 5/9: LLM summarise + categorise ({len(articles)} articles)...")
    articles = llm_summarize_and_categorize(articles, client)

    print("Step 6/9: Applying score bonuses...")
    articles = apply_score_bonuses(articles)

    print("Step 7/9: Applying score gate...")
    articles = apply_score_gate(articles)

    print("Step 8/9: Enforcing diversity and per-category caps...")
    articles = enforce_diversity_and_caps(articles)

    print("Step 9/9: Validating output...")
    _validate_articles(articles)

    for a in articles:
        a["is_featured"] = 1

    print(f"\n  → {len(articles)} articles ready to publish")
    return articles
