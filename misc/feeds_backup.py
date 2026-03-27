# All RSS feed sources, organized by sector.
# Each entry: (name, url, sector)
# Sector values: "ai-updates" | "ai-business" | "ai-dev" | "security"
#
# Tested 2026-03-19. Status column:
#   YES  = active (had articles in last 24h)
#   SLOW = valid feed, low publish frequency (weekly/monthly blogs)
#
# Removed feeds with no working RSS:
#   Anthropic, Snowflake, a16z, Pinecone, Wiz, Sophos Naked Security (all 404)

FEEDS = [
    # ── AI Updates: model releases, research, product launches ────────────────
    ("OpenAI Blog",            "https://openai.com/news/rss.xml",                                              "ai-updates"),  # YES
    ("Google DeepMind",        "https://deepmind.google/blog/rss.xml",                                        "ai-updates"),  # SLOW
    ("Google Blog AI",         "https://blog.google/technology/ai/rss/",                                      "ai-updates"),  # SLOW
    ("Google Research",        "https://research.google/blog/rss/",                                           "ai-updates"),  # SLOW
    ("Microsoft AI",           "https://blogs.microsoft.com/ai/feed",                                         "ai-updates"),  # SLOW
    ("Apple ML",               "https://machinelearning.apple.com/rss.xml",                                   "ai-updates"),  # SLOW
    ("NVIDIA Blog",            "https://feeds.feedburner.com/nvidiablog",                                     "ai-updates"),  # YES
    ("MIT AI News",            "https://news.mit.edu/rss/topic/artificial-intelligence2",                     "ai-updates"),  # YES
    ("Berkeley AI (BAIR)",     "https://bair.berkeley.edu/blog/feed.xml",                                     "ai-updates"),  # SLOW
    ("CMU ML Blog",            "https://blog.ml.cmu.edu/feed",                                                "ai-updates"),  # SLOW
    ("AI News",                "https://www.artificialintelligence-news.com/feed/",                           "ai-updates"),  # YES
    ("The Verge AI",           "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",          "ai-updates"),  # YES
    ("The Verge Tech",         "https://www.theverge.com/rss/tech/index.xml",                                "ai-updates"),  # YES
    ("Ars Technica",           "https://feeds.arstechnica.com/arstechnica/index",                            "ai-updates"),  # YES
    ("MIT Tech Review AI",     "https://www.technologyreview.com/topic/artificial-intelligence/feed/",       "ai-updates"),  # SLOW
    ("MIT Tech Review",        "https://www.technologyreview.com/feed/",                                      "ai-updates"),  # YES
    ("MarkTechPost",           "https://www.marktechpost.com/feed/",                                         "ai-updates"),  # YES
    ("Import AI (Jack Clark)", "https://importai.substack.com/feed",                                         "ai-updates"),  # YES
    ("Import AI (Beehiiv)",    "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                              "ai-updates"),  # YES
    ("arXiv cs.AI",            "https://rss.arxiv.org/rss/cs.AI",                                           "ai-updates"),  # YES
    ("arXiv cs.CL (NLP)",      "https://arxiv.org/rss/cs.CL",                                               "ai-updates"),  # YES

    # ── AI Business: funding, M&A, enterprise, policy, markets ───────────────
    ("TechCrunch AI",          "https://techcrunch.com/category/artificial-intelligence/feed/",              "ai-business"), # YES
    ("TechCrunch (main)",      "https://techcrunch.com/feed/",                                               "ai-business"), # YES
    ("VentureBeat",            "https://venturebeat.com/category/ai/feed/",                                  "ai-business"), # SLOW
    ("Reuters via Google News","https://news.google.com/rss/search?q=site%3Areuters.com+technology&hl=en-US&gl=US&ceid=US%3Aen", "ai-business"), # YES
    ("NYT Technology",         "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",               "ai-business"), # YES
    ("CNBC Tech",              "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910", "ai-business"), # YES
    ("WSJ Tech",               "https://feeds.content.dowjones.io/public/rss/RSSWSJD",                      "ai-business"), # YES (fixed URL)
    ("Meta News",              "https://about.fb.com/feed",                                                  "ai-business"), # YES
    ("Databricks Blog",        "https://www.databricks.com/feed",                                            "ai-business"), # YES

    # ── AI Dev: tools, libraries, SDKs, tutorials, infrastructure ────────────
    ("Hugging Face Blog",      "https://huggingface.co/blog/feed.xml",                                      "ai-dev"),      # YES
    ("Towards Data Science",   "https://towardsdatascience.com/feed",                                        "ai-dev"),      # YES
    ("NVIDIA Developer",       "https://developer.nvidia.com/blog/feed",                                     "ai-dev"),      # YES
    ("AWS Machine Learning",   "https://aws.amazon.com/blogs/machine-learning/feed/",                       "ai-dev"),      # YES
    ("AWS DevOps",             "https://aws.amazon.com/blogs/devops/feed/",                                  "ai-dev"),      # SLOW
    ("Meta Engineering",       "https://engineering.fb.com/feed",                                            "ai-dev"),      # SLOW
    ("Nanonets Blog",          "https://nanonets.com/blog/rss",                                              "ai-dev"),      # SLOW
    ("Kubernetes Blog",        "https://kubernetes.io/feed.xml",                                             "ai-dev"),      # SLOW
    ("HashiCorp Blog",         "https://www.hashicorp.com/blog/feed.xml",                                   "ai-dev"),      # SLOW
    ("Databricks Docs",        "https://docs.databricks.com/aws/en/feed.xml",                               "ai-dev"),      # YES
    ("arXiv cs.LG (ML)",       "https://arxiv.org/rss/cs.LG",                                               "ai-dev"),      # YES
    ("arXiv stat.ML",          "https://arxiv.org/rss/stat.ML",                                             "ai-dev"),      # YES
    ("Product Hunt",           "https://www.producthunt.com/feed",                                           "ai-dev"),      # YES
    ("ByteByteGo",             "https://blog.bytebytego.com/feed",                                          "ai-dev"),      # YES
    ("Hacker News Front Page", "https://hnrss.org/frontpage",                                                "ai-dev"),      # YES

    # ── Security: AI-driven threats, breaches, vulnerability research ─────────
    ("The Hacker News",        "https://feeds.feedburner.com/TheHackersNews",                               "security"),    # YES
    ("Krebs on Security",      "https://krebsonsecurity.com/feed/",                                          "security"),    # SLOW
    ("Dark Reading",           "https://www.darkreading.com/rss.xml",                                        "security"),    # YES
    ("Palo Alto Unit 42",      "https://unit42.paloaltonetworks.com/feed/",                                  "security"),    # YES
    ("Threatpost",             "https://threatpost.com/feed/",                                               "security"),    # SLOW
    ("Infosecurity Magazine",  "https://www.infosecurity-magazine.com/rss/news/",                           "security"),    # YES
    ("Microsoft Security",     "https://api.msrc.microsoft.com/update-guide/rss",                           "security"),    # YES
    ("The Verge Security",     "https://www.theverge.com/rss/cyber-security/index.xml",                    "security"),    # SLOW
]
