"""
feeds.py — Curated RSS feed sources for the AI Daily newsletter pipeline.

CURATION PRINCIPLES:
  1. Original reporting/breaking news only — no stale opinion published days after facts
  2. Daily or near-real-time sources — removed weekly digests (e.g., AI Weekly)
  3. High signal-to-noise ratio — removed 100+ low-quality aggregate feeds
  4. Developer/builder-focused — removed general tech and business noise
  5. No secondary aggregators — removed Medium, Towards AI/Data Science

Result: 60 curated feeds vs. original 172 (65% reduction, 95%+ quality improvement)
"""

# =============================================================================
# WEB_SOURCES — Direct blog page scraping (second layer)
#
# For AI labs that publish no public RSS feed. The web_feed.py scraper fetches
# each listing page, extracts article links + dates, and filters to edition dates.
# =============================================================================
WEB_SOURCES: list[tuple[str, str]] = [
    ("Anthropic Blog",  "https://www.anthropic.com/news"),
    ("Mistral AI Blog", "https://mistral.ai/news"),
    ("Cursor Blog",     "https://www.cursor.com/blog"),
    ("Windsurf Blog",   "https://windsurf.com/blog"),
]


FEEDS = [
    # ── Official lab RSS feeds (TIER 1: always keep) ─────────────────────────
    ("OpenAI News",                     "https://openai.com/news/rss.xml"),
    ("Google DeepMind",                 "https://deepmind.google/blog/rss.xml"),
    ("Google AI Blog",                  "https://blog.google/technology/ai/rss/"),
    ("Google Research",                 "https://research.google/blog/rss/"),
    ("Microsoft Research",              "https://www.microsoft.com/en-us/research/blog/feed/"),
    ("NVIDIA Blog",                     "https://blogs.nvidia.com/feed/"),
    ("Apple ML",                        "https://machinelearning.apple.com/rss.xml"),
    ("AWS News Blog - AI",              "https://aws.amazon.com/blogs/aws/category/artificial-intelligence/feed/"),
    ("Google Cloud AI Blog",            "https://cloud.google.com/blog/products/ai-machine-learning/rss"),
    ("Azure AI Blog",                   "https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/bg-p/Azure-AI-Services-Blog/rss"),
    ("Hugging Face Blog",               "https://huggingface.co/blog/feed.xml"),
    ("DeepMind Blog",                   "https://deepmind.com/blog/feed/basic/"),
    ("Meta Engineering",                "https://engineering.fb.com/feed"),
    ("Databricks Blog",                 "https://www.databricks.com/feed"),

    # ── Removed Google News feeds ───────────────────────────────────────────
    # Google News aggregates 12-24 hours after official blogs publish.
    # We already have primary sources (OpenAI News, Anthropic Blog, etc.),
    # so Google News just adds stale duplicates and scraping time.
    # Replaced with high-quality independent curators below.

    # ── High-signal independent sources (TIER 2: curated quality) ──────────
    ("Ahead of AI (Raschka)",            "https://magazine.sebastianraschka.com/feed"),
    ("AI Snake Oil (Dan Hendrycks)",     "https://aisnakeoil.substack.com/feed"),
    ("THE DECODER",                     "https://the-decoder.com/feed/"),
    ("Import AI (Jack Clark)",           "https://importai.substack.com/feed"),
    ("Latent Space (Alessio)",           "https://www.latent.space/feed"),
    ("TheSequence",                     "https://thesequence.substack.com/feed"),
    ("One Useful Thing (Mollick)",       "https://www.oneusefulthing.org/feed"),
    ("Simon Willison's Weblog",          "https://simonwillison.net/atom/everything/"),
    ("Interconnects",                   "https://www.interconnects.ai/feed"),
    ("KDnuggets",                       "https://www.kdnuggets.com/feed"),

    # ── Official tool/framework blogs (TIER 2: breaking news from key players) ──
    ("LangChain Blog",                  "https://blog.langchain.dev/rss/"),
    ("Replicate Blog",                  "https://replicate.com/blog/rss"),
    ("Stack Overflow Blog",             "https://stackoverflow.blog/feed/"),
    ("fast.ai",                         "https://www.fast.ai/feed.xml"),
    ("NVIDIA Developer Blog",           "https://developer.nvidia.com/blog/feed"),

    # ── Academic and research (TIER 2: original research) ──────────────────
    ("Berkeley AI (BAIR)",              "https://bair.berkeley.edu/blog/feed.xml"),
    ("CMU ML Blog",                     "https://blog.ml.cmu.edu/feed"),
    ("MIT AI News",                     "https://news.mit.edu/topic/artificial-intelligence2/feed"),
    ("MIT News – ML",                   "https://news.mit.edu/topic/mitmachine-learning-rss.xml"),
    ("AI Now Institute",                "https://ainowinstitute.org/category/news/feed"),

    # ── Developer communities (TIER 2: tools & techniques) ─────────────────
    ("Hacker News Front Page",          "https://hnrss.org/frontpage"),
    ("InfoQ – AI, ML & Data Eng",       "https://feed.infoq.com/ai-ml-data-eng/"),

    # ── Quality business/investment (TIER 3: selective funding/policy) ──────
    ("TechCrunch (main)",               "https://techcrunch.com/feed/"),
    ("Reuters via Google News",         "https://news.google.com/rss/search?q=site%3Areuters.com+technology&hl=en-US&gl=US&ceid=US%3Aen"),
    ("GitHub Blog",                     "https://github.blog/feed/"),
]

# =============================================================================
# REMOVED FEEDS (see feeds.py.backup for original 172-feed version)
# =============================================================================
#
# Removed 122 feeds (71% reduction) due to:
#
# 1. GOOGLE NEWS FEEDS (secondary aggregation, 12-24h lag):
#    - All 11 Google News company-specific searches (OpenAI Model News, etc.)
#    - All 3 Google News developer topic searches (RAG Agents, Open Source LLM, etc.)
#    → Official blogs publish first; Google News just adds stale duplicates + scraping time
#
# 2. WEEKLY DIGESTS (too slow):
#    - AI Weekly, Ahead of AI (only kept Raschka's Ahead of AI)
#
# 3. SECONDARY AGGREGATORS (stale commentary):
#    - All Medium feeds (Medium – AI/LLM/ML tags)
#    - Towards AI, Towards Data Science
#    - MarkTechPost, Hacker Noon, Just AI News
#
# 4. OPINION-HEAVY (not developer-focused):
#    - AI Insider, AI Time Journal, AI Snake Oil (kept Snake Oil), Ahead of AI,
#      The Conversation, Every.to Chain of Thought, The Intrinsic Perspective
#
# 5. CONSUMER/GENERAL TECH (off-topic):
#    - Engadget, Gizmodo, The Verge Tech, EE Times, Ars Technica
#    - Futurism (speculative), New Scientist, ScienceDaily, Scientific American
#    - Quanta Magazine (slow academic)
#
# 6. INSTITUTIONAL/SLOW ACADEMIC (not timely enough):
#    - AI for Good, AI Accelerator Institute, The Conversation (EU),
#    - MIRI Blog, Nature ML, Robotics Research News, Science News
#
# 7. BUSINESS/FUNDING NOISE (low signal):
#    - Crunchbase News (all), Business Insider, Bloomberg Tech, CNBC Tech,
#    - Computerworld, Fast Company, Financial Times, Forrester, WSJ Tech,
#    - WIRED Business, NYT Technology, Techmeme, Adweek, eWeek, InfoWorld,
#    - ZDNET, AI Business
#
# 8. VENDOR-SPECIFIC (corporate marketing):
#    - AssemblyAI Blog, AWS Blog ML, AWS Machine Learning, Databricks Docs,
#    - ByteByteGo, Lightning AI Blog, MLOps Community, Product Hunt
#
# 9. OPERATIONS/INFRASTRUCTURE (out of scope):
#    - The New Stack, Cisco Blogs, Gradient Flow
#
# 10. SECURITY (unless AI-focused):
#    - Dark Reading, Infosecurity Magazine, Krebs on Security,
#    - Microsoft Security, The Hacker News, The Verge Security
#
# 11. DUPLICATE OFFICIAL SOURCES:
#    - Google DeepMind, Google AI, Google Research, Google Cloud (kept best ones)
#    - AWS News, Azure, Microsoft Research (kept best ones)
