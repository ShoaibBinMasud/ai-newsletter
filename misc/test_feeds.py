"""
test_feeds.py — Merge all feed URLs, test each one, output a CSV.

Tests:
  1. Is the URL a valid RSS/Atom feed? (feedparser can parse it)
  2. Does it have any entries at all?
  3. How many articles in the last 24h?

Output: data/feeds_status.csv
"""

import csv
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests

sys.path.insert(0, str(Path(__file__).parent))

# ── All feeds: (name, url, sector) ────────────────────────────────────────────
# Merged from feeds.py + user-supplied list, duplicates removed.
ALL_FEEDS = [
    # ── AI Updates ─────────────────────────────────────────────────────────────
    ("OpenAI Blog",              "https://openai.com/news/rss.xml",                                                          "ai-updates"),
    ("Anthropic News",           "https://www.anthropic.com/rss.xml",                                                        "ai-updates"),
    ("Google DeepMind",          "https://deepmind.google/blog/rss.xml",                                                     "ai-updates"),
    ("DeepMind (alt)",           "https://www.deepmind.com/blog/rss",                                                        "ai-updates"),
    ("Google Blog AI",           "https://blog.google/technology/ai/rss/",                                                   "ai-updates"),
    ("Google Research",          "https://research.google/blog/rss/",                                                        "ai-updates"),
    ("Microsoft AI",             "https://blogs.microsoft.com/ai/feed",                                                      "ai-updates"),
    ("Apple ML",                 "https://machinelearning.apple.com/rss.xml",                                                "ai-updates"),
    ("NVIDIA Blog",              "https://feeds.feedburner.com/nvidiablog",                                                  "ai-updates"),
    ("MIT AI News",              "https://news.mit.edu/rss/topic/artificial-intelligence2",                                  "ai-updates"),
    ("Berkeley AI (BAIR)",       "https://bair.berkeley.edu/blog/feed.xml",                                                  "ai-updates"),
    ("CMU ML Blog",              "https://blog.ml.cmu.edu/feed",                                                             "ai-updates"),
    ("AI News",                  "https://www.artificialintelligence-news.com/feed/",                                        "ai-updates"),
    ("The Verge AI",             "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",                       "ai-updates"),
    ("The Verge Tech",           "https://www.theverge.com/rss/tech/index.xml",                                             "ai-updates"),
    ("Ars Technica",             "https://feeds.arstechnica.com/arstechnica/index",                                         "ai-updates"),
    ("MIT Tech Review AI",       "https://www.technologyreview.com/topic/artificial-intelligence/feed/",                    "ai-updates"),
    ("MIT Tech Review",          "https://www.technologyreview.com/feed/",                                                   "ai-updates"),
    ("MarkTechPost",             "https://www.marktechpost.com/feed/",                                                      "ai-updates"),
    ("Import AI (Jack Clark)",   "https://jack-clark.net/feed.xml",                                                          "ai-updates"),
    ("Import AI (Beehiiv)",      "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                                            "ai-updates"),
    ("arXiv cs.AI",              "https://rss.arxiv.org/rss/cs.AI",                                                         "ai-updates"),
    ("arXiv cs.CL (NLP)",        "https://arxiv.org/rss/cs.CL",                                                             "ai-updates"),

    # ── AI Business ────────────────────────────────────────────────────────────
    ("TechCrunch AI",            "https://techcrunch.com/category/artificial-intelligence/feed/",                           "ai-business"),
    ("TechCrunch (main)",        "https://techcrunch.com/feed/",                                                            "ai-business"),
    ("VentureBeat",              "https://venturebeat.com/category/ai/feed/",                                               "ai-business"),
    ("Reuters via Google News",  "https://news.google.com/rss/search?q=site%3Areuters.com+technology&hl=en-US&gl=US&ceid=US%3Aen", "ai-business"),
    ("NYT Technology",           "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",                             "ai-business"),
    ("CNBC Tech",                "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",     "ai-business"),
    ("WSJ Tech",                 "https://feeds.a.dj.com/rss/RSSWSJD.xml",                                                 "ai-business"),
    ("WSJ Tech (alt)",           "https://feeds.content.dowjones.io/public/rss/RSSWSJD",                                   "ai-business"),
    ("Meta News",                "https://about.fb.com/feed",                                                               "ai-business"),
    ("Databricks Blog",          "https://www.databricks.com/feed",                                                         "ai-business"),
    ("Snowflake Blog",           "https://www.snowflake.com/blog/feed/",                                                    "ai-business"),
    ("a16z Blog",                "https://a16z.com/feed/",                                                                  "ai-business"),

    # ── AI Dev ─────────────────────────────────────────────────────────────────
    ("Hugging Face Blog",        "https://huggingface.co/blog/feed.xml",                                                    "ai-dev"),
    ("Towards Data Science",     "https://towardsdatascience.com/feed",                                                     "ai-dev"),
    ("NVIDIA Developer",         "https://developer.nvidia.com/blog/feed",                                                  "ai-dev"),
    ("AWS Machine Learning",     "https://aws.amazon.com/blogs/machine-learning/feed/",                                     "ai-dev"),
    ("AWS DevOps",               "https://aws.amazon.com/blogs/devops/feed/",                                               "ai-dev"),
    ("Meta Engineering",         "https://engineering.fb.com/feed",                                                         "ai-dev"),
    ("Pinecone Blog",            "https://www.pinecone.io/blog/rss.xml",                                                    "ai-dev"),
    ("Nanonets Blog",            "https://nanonets.com/blog/rss",                                                           "ai-dev"),
    ("Kubernetes Blog",          "https://kubernetes.io/feed.xml",                                                          "ai-dev"),
    ("HashiCorp Blog",           "https://www.hashicorp.com/blog/feed.xml",                                                 "ai-dev"),
    ("Databricks Docs",          "https://docs.databricks.com/aws/en/feed.xml",                                             "ai-dev"),
    ("arXiv cs.LG (ML)",         "https://arxiv.org/rss/cs.LG",                                                            "ai-dev"),
    ("arXiv stat.ML",            "https://arxiv.org/rss/stat.ML",                                                           "ai-dev"),
    ("Product Hunt",             "https://www.producthunt.com/feed",                                                        "ai-dev"),
    ("ByteByteGo",               "https://blog.bytebytego.com/feed",                                                       "ai-dev"),
    ("Hacker News Front Page",   "https://hnrss.org/frontpage",                                                             "ai-dev"),

    # ── Security ───────────────────────────────────────────────────────────────
    ("The Hacker News",          "https://feeds.feedburner.com/TheHackersNews",                                             "security"),
    ("Krebs on Security",        "https://krebsonsecurity.com/feed/",                                                       "security"),
    ("Dark Reading",             "https://www.darkreading.com/rss.xml",                                                     "security"),
    ("Palo Alto Unit 42",        "https://unit42.paloaltonetworks.com/feed/",                                               "security"),
    ("Wiz Blog",                 "https://www.wiz.io/blog/rss.xml",                                                        "security"),
    ("Sophos (Naked Security)",  "https://nakedsecurity.sophos.com/feed/",                                                  "security"),
    ("Threatpost",               "https://threatpost.com/feed/",                                                            "security"),
    ("Infosecurity Magazine",    "https://www.infosecurity-magazine.com/rss/news/",                                         "security"),
    ("Microsoft Security",       "https://api.msrc.microsoft.com/update-guide/rss",                                        "security"),
    ("The Verge Security",       "https://www.theverge.com/rss/cyber-security/index.xml",                                   "security"),
]

LOOKBACK_HOURS = 24
TIMEOUT = 8

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
}


def test_feed(name: str, url: str) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    result = {
        "name": name,
        "url": url,
        "is_valid_rss": False,
        "total_entries": 0,
        "entries_24h": 0,
        "status": "",
        "note": "",
    }

    try:
        # Use requests so we can control timeout + headers, then pass to feedparser
        resp = requests.get(url, timeout=TIMEOUT, headers=_HEADERS, allow_redirects=True)
        result["status"] = str(resp.status_code)

        if resp.status_code != 200:
            result["note"] = f"HTTP {resp.status_code}"
            return result

        feed = feedparser.parse(resp.content)

        if feed.bozo and not feed.entries:
            result["note"] = f"Parse error: {getattr(feed, 'bozo_exception', 'unknown')}"
            return result

        result["is_valid_rss"] = True
        result["total_entries"] = len(feed.entries)

        recent = 0
        for entry in feed.entries:
            for attr in ("published_parsed", "updated_parsed"):
                t = getattr(entry, attr, None)
                if t:
                    try:
                        pub = datetime(*t[:6], tzinfo=timezone.utc)
                        if pub >= cutoff:
                            recent += 1
                    except Exception:
                        pass
                    break

        result["entries_24h"] = recent
        result["note"] = "OK" if recent > 0 else ("feed ok, no recent articles" if result["total_entries"] > 0 else "feed empty")

    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
        result["note"] = "Could not connect"
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["note"] = f"Timed out after {TIMEOUT}s"
    except Exception as e:
        result["status"] = "error"
        result["note"] = str(e)[:80]

    return result


def works(r: dict) -> str:
    if r["entries_24h"] > 0:
        return "YES"
    if r["is_valid_rss"] and r["total_entries"] > 0:
        return "SLOW"   # valid feed, just quiet today
    return "NO"


def main():
    output = Path("data/feeds_status.csv")
    output.parent.mkdir(exist_ok=True)

    print(f"Testing {len(ALL_FEEDS)} feeds...\n")
    rows = []

    for i, (name, url, sector) in enumerate(ALL_FEEDS, 1):
        print(f"[{i:02d}/{len(ALL_FEEDS)}] {name:<30} ", end="", flush=True)
        r = test_feed(name, url)
        w = works(r)
        print(f"{w:<5}  {r['entries_24h']} articles/24h  {r['note']}")
        rows.append({
            "name":          name,
            "url":           url,
            "sector":        sector,
            "works":         w,
            "entries_24h":   r["entries_24h"],
            "total_entries": r["total_entries"],
            "http_status":   r["status"],
            "note":          r["note"],
        })

    # ── Write CSV ──────────────────────────────────────────────────────────────
    fieldnames = ["name", "url", "sector", "works", "entries_24h", "total_entries", "http_status", "note"]
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ────────────────────────────────────────────────────────────────
    yes   = sum(1 for r in rows if r["works"] == "YES")
    slow  = sum(1 for r in rows if r["works"] == "SLOW")
    no    = sum(1 for r in rows if r["works"] == "NO")
    print(f"\n{'='*60}")
    print(f"YES (active today): {yes}  |  SLOW (valid, quiet): {slow}  |  NO (broken): {no}")
    print(f"Saved -> {output}")


if __name__ == "__main__":
    main()
