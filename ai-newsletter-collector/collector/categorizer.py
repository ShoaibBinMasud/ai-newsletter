"""
collector/categorizer.py — Keyword-based sector categoriser.

Used only for feeds declared with sector="auto" in feeds.py.
All other feeds are pre-assigned to a sector and this module is skipped.

Scoring works by counting how many sector keywords appear in the combined
title + source string. The sector with the highest count wins. On ties,
sectors are preferred in the order they appear in SECTOR_KEYWORDS
(ai-updates is listed first, so it wins ties as the most general bucket).

Sectors
-------
  ai-updates  — Model releases, research, product launches
  ai-business — Funding, acquisitions, market moves, regulation
  ai-dev      — Frameworks, tools, tutorials, open-source
  security    — Breaches, threats, ransomware, vulnerabilities

To add a new sector: add one entry to SECTOR_KEYWORDS and add the
corresponding context/subcategory entries in prompts.py.
"""

from __future__ import annotations

# ── Sector keyword mapping ────────────────────────────────────────────────────
# A single ordered dict is the single source of truth for all sectors.
# Ordering matters: the first sector wins on ties (ai-updates is the
# general fallback, so it is listed first).
#
# Keep keywords focused on strong discriminating signals. Omit generic
# words shared across sectors (e.g. "AI", "technology") — they add noise
# without helping distinguish between sectors.

SECTOR_KEYWORDS: dict[str, frozenset[str]] = {
    "ai-updates": frozenset({
        "release", "released", "launch", "launched", "announce", "announced",
        "model", "gpt", "claude", "gemini", "llama", "mistral", "benchmark",
        "multimodal", "reasoning", "agent", "upgrade", "update", "new version",
        "openai", "anthropic", "google deepmind", "meta ai", "xai", "cohere",
        "alignment", "safety", "capability", "evaluation", "fine-tuning",
    }),
    "ai-business": frozenset({
        "funding", "raises", "raised", "acquisition", "acquires", "acquired",
        "partnership", "valuation", "investment", "series a", "series b",
        "ipo", "merger", "revenue", "enterprise", "databricks", "snowflake",
        "salesforce", "microsoft", "nvidia", "arm", "startup", "venture",
        "regulation", "policy", "legislation", "antitrust", "executive order",
    }),
    "ai-dev": frozenset({
        "paper", "arxiv", "tutorial", "how-to", "guide", "github", "repo",
        "repository", "open source", "open-source", "dataset", "fine-tun",
        "training", "inference", "framework", "library", "tool", "sdk",
        "trending", "implementation", "deploy", "api", "benchmark", "rag",
        "langchain", "hugging face", "pytorch", "tensorflow", "transformer",
    }),
    "security": frozenset({
        "breach", "hack", "hacked", "hacking", "ransomware", "malware",
        "phishing", "vulnerability", "cve", "exploit", "zero-day", "zero day",
        "cybersecurity", "cyber", "threat", "attack", "data leak", "leaked",
        "encryption", "firewall", "apt", "nation-state", "espionage",
        "compliance", "incident", "forensics", "intrusion", "backdoor",
        "botnet", "ddos", "social engineering", "credential", "identity theft",
    }),
}

# The first key in SECTOR_KEYWORDS acts as the default (wins ties and
# catches articles that match no keywords). Named here for clarity.
_DEFAULT_SECTOR: str = next(iter(SECTOR_KEYWORDS))


# ── Categoriser function ──────────────────────────────────────────────────────

def categorize(title: str, source: str) -> str:
    """
    Return the most likely sector for an article given its title and source.

    Scoring: count keyword matches in the lowercased (title + source) string.
    The sector with the highest count wins. On ties or no match, the default
    sector ("ai-updates") is returned.

    Parameters
    ----------
    title  : Article headline from the RSS feed
    source : Feed / source name (e.g. "Krebs on Security", "TechCrunch")

    Returns
    -------
    Sector string: "ai-updates" | "ai-business" | "ai-dev" | "security"
    """
    text = f"{title} {source}".lower()

    scores = {
        sector: sum(1 for kw in keywords if kw in text)
        for sector, keywords in SECTOR_KEYWORDS.items()
    }

    best_score = max(scores.values())

    # No keywords matched at all — return the default sector.
    if best_score == 0:
        return _DEFAULT_SECTOR

    # Return the first sector (by definition order) that achieved the top score.
    # Since SECTOR_KEYWORDS is ordered and ai-updates is first, it naturally
    # wins ties — no lambda hack needed.
    return next(sector for sector, score in scores.items() if score == best_score)
