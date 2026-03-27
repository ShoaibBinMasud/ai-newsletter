"""
check_feeds.py — scrape + validate RSS feeds from two external sources,
then merge with existing feeds.py into a final feed_status CSV.

Outputs:
  data/new_feeds_candidates.csv  — deduplicated feeds from feedspot + github, with validity
  data/feed_status.csv           — final: existing feeds.py feeds + new valid feeds
"""

import csv
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# ── Scraped data ──────────────────────────────────────────────────────────────

FEEDSPOT_FEEDS = [
    ("Google Research Blog",                 "https://research.google/blog/rss/",                                              "news"),
    ("OpenAI News",                          "https://openai.com/news/rss.xml",                                                "news"),
    ("BAIR (Berkeley AI Research) Blog",     "https://bair.berkeley.edu/blog/feed.xml",                                        "news"),
    ("MIT News - Artificial Intelligence",   "https://news.mit.edu/rss/topic/artificial-intelligence2",                        "news"),
    ("MIT Technology Review - AI",           "https://www.technologyreview.com/topic/artificial-intelligence/feed",            "news"),
    ("MIRI Blog",                            "https://intelligence.org/feed/",                                                 "news"),
    ("O'Reilly Media - AI & ML",             "https://www.oreilly.com/radar/topics/ai-ml/feed/index.xml",                     "news"),
    ("KDnuggets",                            "https://www.kdnuggets.com/feed",                                                 "news"),
    ("TechCrunch - AI",                      "https://techcrunch.com/category/artificial-intelligence/feed/",                 "news"),
    ("VentureBeat - AI",                     "https://venturebeat.com/category/ai/feed/",                                     "news"),
    ("Financial Times - AI",                 "https://www.ft.com/artificial-intelligence?format=rss",                         "news"),
    ("The New York Times - AI",              "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/spotlight/artificial-intelligence/rss.xml", "news"),
    ("WIRED - Artificial Intelligence",      "https://www.wired.com/feed/tag/ai/latest/rss",                                  "news"),
    ("Ars Technica - AI",                    "https://arstechnica.com/ai/feed/",                                              "news"),
    ("The Guardian - AI",                    "https://www.theguardian.com/technology/artificialintelligenceai/rss",            "news"),
    ("Science News - AI",                    "https://www.sciencenews.org/topic/artificial-intelligence/feed",                 "news"),
    ("ScienceDaily - AI News",               "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",   "news"),
    ("Microsoft - AI",                       "https://news.microsoft.com/source/topics/ai/feed/",                             "news"),
    ("AWS News Blog - AI",                   "https://aws.amazon.com/blogs/aws/category/artificial-intelligence/feed/",       "news"),
    ("InfoWorld - AI",                       "https://www.infoworld.com/artificial-intelligence/feed/",                       "news"),
    ("Computerworld - AI",                   "https://www.computerworld.com/artificial-intelligence/feed/",                   "news"),
    ("Fast Company - AI",                    "https://www.fastcompany.com/section/artificial-intelligence/rss",               "news"),
    ("The Verge - AI",                       "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",             "news"),
    ("Live Science - AI",                    "https://www.livescience.com/feeds/tag/artificial-intelligence",                 "news"),
    ("Government Technology - AI",           "https://www.govtech.com/artificial-intelligence.rss",                          "news"),
    ("Analytics Vidhya Blog",                "https://www.analyticsvidhya.com/feed/",                                        "news"),
    ("Machine Learning Mastery Blog",        "https://machinelearningmastery.com/blog/feed/",                                 "news"),
    ("AI Weekly",                            "https://aiweekly.co/issues.rss",                                                "news"),
    ("AIhub",                                "https://aihub.org/feed/?cat=-473",                                              "news"),
    ("AI Summer",                            "https://theaisummer.com/feed.xml",                                              "news"),
    ("RStudio AI Blog",                      "https://blogs.rstudio.com/ai/index.xml",                                        "news"),
    ("DataRobot Blog",                       "https://www.datarobot.com/blog/feed/",                                          "news"),
    ("SAS - AI",                             "https://blogs.sas.com/content/topic/artificial-intelligence/feed/",             "news"),
    ("MarkTechPost",                         "https://www.marktechpost.com/feed/",                                            "news"),
    ("Big Data Analytics News - AI",         "https://bigdataanalyticsnews.com/category/artificial-intelligence/feed/",      "news"),
    ("Unite.AI",                             "https://www.unite.ai/feed/",                                                    "news"),
    ("AI News (artificialintelligence-news.com)", "https://www.artificialintelligence-news.com/feed/",                       "news"),
    ("AIwire",                               "https://www.aiwire.net/feed/",                                                  "news"),
    ("Crunchbase News - AI",                 "https://news.crunchbase.com/sections/ai/feed/",                                 "news"),
    ("eWeek - AI",                           "https://www.eweek.com/feed/",                                                   "news"),
    ("France 24 - AI",                       "https://www.france24.com/en/tag/artificial-intelligence/rss",                  "news"),
    ("The Indian Express - AI",              "https://indianexpress.com/section/technology/artificial-intelligence/feed/",   "news"),
    ("Mint - AI",                            "https://www.livemint.com/rss/AI",                                               "news"),
    ("GeekWire - AI",                        "https://www.geekwire.com/tag/ai/feed/",                                         "news"),
    ("Adweek - AI",                          "https://www.adweek.com/category/artificial-intelligence/feed/",                 "news"),
    ("Artificial Lawyer",                    "https://www.artificiallawyer.com/feed/",                                        "news"),
    ("Marketing AI Institute Blog",          "https://www.marketingaiinstitute.com/blog/rss.xml",                             "news"),
    ("The Rundown AI",                       "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                                  "news"),
    ("Data Machina",                         "https://datamachina.substack.com/feed",                                         "news"),
    ("Another Datum",                        "https://anotherdatum.com/feeds/all.atom.xml?format=xml",                       "news"),
    ("Dan Rose AI Blog",                     "https://www.danrose.ai/blog?format=rss",                                        "news"),
    ("Kavita Ganesan",                       "http://kavita-ganesan.com/feed/",                                               "news"),
    ("DatumBox",                             "http://blog.datumbox.com/feed/",                                                "news"),
    ("Digital Thought Disruption",           "https://digitalthoughtdisruption.com/feed/",                                   "news"),
    ("Becoming Human",                       "https://becominghuman.ai/feed",                                                 "news"),
    ("AI Time Journal",                      "https://www.aitimejournal.com/feed/",                                           "news"),
    ("Contextual AI Blog",                   "https://contextual.ai/blog/feed/",                                              "news"),
    ("Aleph Alpha Blog",                     "https://aleph-alpha.com/feed/",                                                 "news"),
    ("Clarifai Blog",                        "https://www.clarifai.com/blog/rss.xml",                                         "news"),
    ("Kore.ai",                              "https://blog.kore.ai/rss.xml",                                                  "news"),
    ("Nanonets Blog",                        "https://nanonets.com/blog/rss/",                                                "news"),
    ("Unbabel Blog",                         "https://unbabel.com/category/blog/feed/",                                       "news"),
    ("Qudata",                               "https://qudata.com/en/news/rss.xml",                                            "news"),
    ("ELEDIA E-AIR",                         "http://www.eledia.org/e-air/feed/",                                             "news"),
    ("DLabs.AI Blog",                        "https://dlabs.ai/feed/",                                                        "news"),
    ("DeepCognition.ai Blog",                "https://deepcognition.ai/feed/",                                                "news"),
    ("insideAI News",                        "https://insideainews.com/feed/",                                                 "news"),
    ("DailyAI",                              "https://dailyai.com/feed/",                                                     "news"),
    ("AI Insider",                           "https://theaiinsider.tech/feed/",                                               "news"),
    ("Just AI News",                         "https://justainews.com/feed/",                                                  "news"),
    ("AI 2 People",                          "https://ai2people.com/feed/",                                                   "news"),
    ("Zeroth Principles of AI",              "https://zerothprinciples.substack.com/feed",                                    "news"),
    ("Marek Rosa / GoodAI Blog",             "https://blog.marekrosa.org/feed/",                                              "news"),
    ("MetaDevo AI Blog",                     "https://metadevo.com/feed/",                                                    "news"),
    ("TechSpective - AI",                    "https://techspective.net/category/technology/artificial-intelligence/feed/",   "news"),
    ("NeuroSYS Blog - AI",                   "https://neurosys.com/blog/category/ai/feed",                                    "news"),
    ("Fusemachines Insights",                "https://insights.fusemachines.com/feed/",                                       "news"),
    ("Vectra AI Blog",                       "https://www.vectra.ai/blog/rss.xml",                                            "news"),
    ("Copyleaks Blog",                       "https://copyleaks.com/blog/feed",                                               "news"),
    ("GPTZero Blog",                         "https://gptzero.me/news/rss/",                                                  "news"),
    ("Isentia",                              "https://www.isentia.com/feed/",                                                  "news"),
    ("viAct.ai Blog",                        "https://www.viact.ai/blog-feed.xml",                                            "news"),
    ("Vue.ai Blog",                          "https://www.vue.ai/blog/feed/",                                                 "news"),
    ("Yseop Blog",                           "https://yseop.com/category/blog/feed/",                                         "news"),
    ("SAAL",                                 "https://saal.ai/feed/",                                                          "news"),
    ("KocharTech",                           "https://www.kochartech.com/feed/",                                               "news"),
    ("Spritle Blog",                         "https://www.spritle.com/blog/feed/",                                             "news"),
    ("Shaip Blog",                           "https://www.shaip.com/feed/",                                                    "news"),
    ("Cogito Tech Blog",                     "https://www.cogitotech.com/feed/",                                               "news"),
    ("Artisse AI Blog",                      "https://artisse.ai/feed/",                                                       "news"),
    ("Dxcover Blog",                         "https://www.dxcover.com/feed/",                                                  "news"),
    ("Neysa Newsroom",                       "https://neysa.ai/feed/",                                                         "news"),
    ("Pandio Blog",                          "https://pandio.com/feed/",                                                       "news"),
    ("Yatter Blog",                          "https://yatter.in/feed/",                                                        "news"),
    ("AI Revolution Blog",                   "https://airevolution.blog/feed/",                                                "news"),
    ("AICorr.com",                           "https://aicorr.com/feed/",                                                       "news"),
    ("1redDrop - AI",                        "https://1reddrop.com/category/artificial-intelligence/feed/",                   "news"),
    ("Top Marketing AI",                     "https://topmarketingai.com/feed/",                                               "news"),
    ("Edmonton Journal - AI",                "https://edmontonjournal.com/tag/artificial-intelligence/feed.xml",              "news"),
    ("Scripps News - AI",                    "https://www.scrippsnews.com/science-and-tech/artificial-intelligence.rss",      "news"),
    ("AI nyheter (aitool.se)",               "https://nyheter.aitool.se/feed/",                                               "news"),
    ("Robot Writers AI",                     "https://robotwritersai.com/feed/",                                               "news"),
    ("Francesco Corea (Medium)",             "https://medium.com/feed/@Francesco_AI",                                         "news"),
    ("Archie.AI (Medium)",                   "https://medium.com/feed/archieai",                                               "news"),
    ("Artificial-Intelligence.Blog",         "https://www.artificial-intelligence.blog/ai-news?format=rss",                   "news"),
    ("AIIOT Talk",                           "https://www.aiiottalk.com/feed/",                                                "news"),
    ("Computational Intelligence (Blogspot)","http://computational-intelligence.blogspot.com/feeds/posts/default",            "news"),
    ("Cisco Blogs - AI",                     "https://blogs.cisco.com/ai/feed",                                                "news"),
    ("AWS Blog - Machine Learning/AI",       "https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/feed/", "news"),
    ("AI for Good Blog",                     "https://aiforgood.itu.int/feed/",                                                "news"),
    ("Theodo Data & AI Blog",                "https://data-ai.theodo.com/en/technical-blog/rss.xml",                          "news"),
    ("Analytics India Magazine - AI News",   "https://analyticsindiamag.com/ai-news-updates/feed/",                           "news"),
    ("The Conversation - AI",                "https://theconversation.com/topics/artificial-intelligence-ai-90/articles.atom","news"),
    ("Federal News Network - AI",            "https://federalnewsnetwork.com/category/technology-main/artificial-intelligence/feed/", "news"),
    ("Berkshire Grey Blog",                  "https://www.berkshiregrey.com/feed/",                                            "news"),
]

GITHUB_NEWS_FEEDS = [
    ("404 Media",                            "https://www.404media.co/rss",                                                    "news"),
    ("Ahead of AI",                          "https://magazine.sebastianraschka.com/feed",                                     "news"),
    ("AI Accelerator Institute",             "https://aiacceleratorinstitute.com/rss/",                                        "news"),
    ("AI – AI-TechPark",                     "https://ai-techpark.com/category/ai/feed/",                                      "news"),
    ("AI Archives – KnowTechie",             "https://knowtechie.com/category/ai/feed/",                                       "news"),
    ("AI Business",                          "https://aibusiness.com/rss.xml",                                                  "news"),
    ("AIModels.fyi",                         "https://aimodels.substack.com/feed",                                              "news"),
    ("AI News – VentureBeat",                "https://venturebeat.com/category/ai/feed/",                                      "news"),
    ("AI Now Institute",                     "https://ainowinstitute.org/category/news/feed",                                   "news"),
    ("AI – SiliconANGLE",                    "https://siliconangle.com/category/ai/feed",                                      "news"),
    ("AI Snake Oil",                         "https://aisnakeoil.substack.com/feed",                                           "news"),
    ("AI – Uber Engineering Blog",           "https://eng.uber.com/category/articles/ai/feed",                                 "news"),
    ("Anaconda Blog",                        "https://www.anaconda.com/blog/feed",                                              "news"),
    ("Analytics India Magazine",             "https://analyticsindiamag.com/feed/",                                            "news"),
    ("Announcements – Stability AI",         "https://stability.ai/blog?format=rss",                                           "news"),
    ("Ars Technica – All content",           "https://feeds.arstechnica.com/arstechnica/index",                                "news"),
    ("Artificial intelligence – The Conversation (EU)", "https://theconversation.com/europe/topics/artificial-intelligence-ai-90/articles.atom", "news"),
    ("Artificial intelligence – The Guardian","https://www.theguardian.com/technology/artificialintelligenceai/rss",           "news"),
    ("Artificial intelligence – SpaceNews",  "https://spacenews.com/tag/artificial-intelligence/feed/",                       "news"),
    ("Artificial Intelligence – Futurism",   "https://futurism.com/categories/ai-artificial-intelligence/feed",               "news"),
    ("Artificial Intelligence Latest (WIRED)","https://www.wired.com/feed/tag/ai/latest/rss",                                  "news"),
    ("Artificial Intelligence News – ScienceDaily","https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml","news"),
    ("Artificial Intelligence – TechRepublic","https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/",         "news"),
    ("Artificialis – Medium",                "https://medium.com/feed/artificialis",                                           "news"),
    ("Big Data – SiliconANGLE",              "https://siliconangle.com/category/big-data/feed",                               "news"),
    ("Machine Learning Mastery Blog",        "https://machinelearningmastery.com/blog/feed",                                   "news"),
    ("David Stutz Blog",                     "https://davidstutz.de/category/blog/feed",                                       "news"),
    ("Blog Content – TOGETHER",              "https://www.together.xyz/blog?format=rss",                                       "news"),
    ("Blog – neptune.ai",                    "https://neptune.ai/blog/feed",                                                    "news"),
    ("EleutherAI Blog",                      "https://blog.eleuther.ai/index.xml",                                             "news"),
    ("Blog – PyImageSearch",                 "https://pyimagesearch.com/blog/feed",                                             "news"),
    ("Bloomberg Technology",                 "https://feeds.bloomberg.com/technology/news.rss",                                "news"),
    ("Business Insider",                     "https://feeds.businessinsider.com/custom/all",                                   "news"),
    ("Business Latest (WIRED)",              "https://www.wired.com/feed/category/business/latest/rss",                       "news"),
    ("Chain of Thought (every.to)",          "https://every.to/chain-of-thought/feed.xml",                                     "news"),
    ("Chip Huyen",                           "https://huyenchip.com/feed",                                                     "news"),
    ("Computerworld",                        "http://www.computerworld.com/index.rss",                                         "news"),
    ("Context by Cohere",                    "https://txt.cohere.ai/rss/",                                                     "news"),
    ("Crunchbase News",                      "https://news.crunchbase.com/feed",                                               "news"),
    ("cs.CL updates on arXiv.org",           "https://arxiv.org/rss/cs.CL",                                                    "news"),
    ("cs.CV updates on arXiv.org",           "https://arxiv.org/rss/cs.CV",                                                    "news"),
    ("cs.LG updates on arXiv.org",           "https://arxiv.org/rss/cs.LG",                                                    "news"),
    ("DagsHub Blog",                         "https://dagshub.com/blog/rss/",                                                  "news"),
    ("Dark Reading",                         "https://www.darkreading.com/rss_simple.asp",                                     "news"),
    ("Databricks",                           "https://www.databricks.com/feed",                                                "news"),
    ("Datafloq",                             "https://datafloq.com/feed/?post_type=post",                                      "news"),
    ("Data Machina",                         "https://datamachina.substack.com/feed",                                          "news"),
    ("Datanami",                             "https://www.datanami.com/feed/",                                                  "news"),
    ("DebuggerCafe",                         "https://debuggercafe.com/feed/",                                                  "news"),
    ("Deephaven Blog",                       "https://deephaven.io/blog/rss.xml",                                              "news"),
    ("DeepMind Blog",                        "https://deepmind.com/blog/feed/basic/",                                          "news"),
    ("Deep Tech – Tech.eu",                  "https://tech.eu/category/deep-tech/feed",                                        "news"),
    ("Department of Product",                "https://departmentofproduct.substack.com/feed",                                  "news"),
    ("DEV Community",                        "https://dev.to/feed",                                                             "news"),
    ("EE Times",                             "https://www.eetimes.com/feed",                                                    "news"),
    ("Engadget",                             "https://www.engadget.com/rss.xml",                                                "news"),
    ("Eugene Yan",                           "https://eugeneyan.com/rss/",                                                      "news"),
    ("Explosion",                            "https://explosion.ai/feed",                                                       "news"),
    ("Freethink",                            "https://www.freethink.com/feed/all",                                              "news"),
    ("Generational",                         "https://www.generational.pub/feed",                                               "news"),
    ("Forrester – AI",                       "https://www.forrester.com/blogs/category/artificial-intelligence-ai/feed",      "news"),
    ("gHacks Technology News",               "https://www.ghacks.net/feed/",                                                    "news"),
    ("Gizmodo",                              "https://gizmodo.com/rss",                                                         "news"),
    ("Global News – AI",                     "https://globalnews.ca/tag/artificial-intelligence/feed",                         "news"),
    ("Google AI Blog",                       "http://googleaiblog.blogspot.com/atom.xml",                                      "news"),
    ("Gradient Flow",                        "https://gradientflow.com/feed/",                                                  "news"),
    ("Hacker Noon – AI",                     "https://hackernoon.com/tagged/ai/feed",                                          "news"),
    ("HealthTech Magazine",                  "https://feeds.feedburner.com/HealthTechMagazine",                                 "news"),
    ("Hugging Face Blog",                    "https://huggingface.co/blog/feed.xml",                                           "news"),
    ("IEEE Spectrum – AI",                   "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",              "news"),
    ("InfoQ – AI, ML & Data Engineering",    "https://feed.infoq.com/ai-ml-data-eng/",                                        "news"),
    ("InfoWorld Analytics",                  "https://www.infoworld.com/category/analytics/index.rss",                        "news"),
    ("InfoWorld Machine Learning",           "https://www.infoworld.com/category/machine-learning/index.rss",                 "news"),
    ("insideBIGDATA",                        "https://insidebigdata.com/feed",                                                  "news"),
    ("Interconnects",                        "https://www.interconnects.ai/feed",                                               "news"),
    ("International Business Times",         "https://www.ibtimes.com/rss",                                                    "news"),
    ("JMLR",                                 "https://www.jmlr.org/jmlr.xml",                                                   "news"),
    ("KDnuggets",                            "https://www.kdnuggets.com/feed",                                                  "news"),
    ("LangChain",                            "https://blog.langchain.dev/rss/",                                                 "news"),
    ("Last Week in AI",                      "https://lastweekin.ai/feed",                                                      "news"),
    ("Latent Space",                         "https://www.latent.space/feed",                                                   "news"),
    ("Latest from Sifted",                   "https://sifted.eu/feed/?post_type=article",                                      "news"),
    ("ZDNET – AI",                           "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",                   "news"),
    ("ZDNET – Big Data",                     "https://www.zdnet.com/topic/big-data/rss.xml",                                   "news"),
    ("Lightning AI",                         "https://lightning.ai/pages/feed/",                                                "news"),
    ("Machine learning – Nature",            "https://www.nature.com/subjects/machine-learning.rss",                          "news"),
    ("ML@CMU Blog",                          "https://blog.ml.cmu.edu/feed",                                                    "news"),
    ("MarkTechPost",                         "https://www.marktechpost.com/feed",                                               "news"),
    ("Microsoft Research",                   "https://www.microsoft.com/en-us/research/feed/",                                 "news"),
    ("Mila",                                 "https://mila.quebec/en/feed/",                                                    "news"),
    ("MIT News – Machine Learning",          "https://news.mit.edu/topic/mitmachine-learning-rss.xml",                        "news"),
    ("MIT Technology Review",                "https://www.technologyreview.com/feed/",                                         "news"),
    ("Mozilla Foundation Blog",              "https://foundation.mozilla.org/en/blog/rss/",                                   "news"),
    ("New Scientist – Technology",           "https://www.newscientist.com/subject/technology/feed/",                         "news"),
    ("News on AI/ML – TechXplore (phys.org)","https://phys.org/rss-feed/technology-news/machine-learning-ai/",               "news"),
    ("News on AI/ML – TechXplore",           "https://techxplore.com/rss-feed/machine-learning-ai-news/",                    "news"),
    ("AssemblyAI Blog",                      "https://www.assemblyai.com/blog/rss/",                                           "news"),
    ("Nicholas Carlini",                     "https://nicholas.carlini.com/writing/feed.xml",                                  "news"),
    ("NVIDIA Technical Blog",                "https://developer.nvidia.com/blog/feed",                                         "news"),
    ("NYT – Technology",                     "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",                   "news"),
    ("One Useful Thing",                     "https://www.oneusefulthing.org/feed",                                             "news"),
    ("OpenAI Blog",                          "https://openai.com/blog/rss/",                                                    "news"),
    ("Paperspace Blog",                      "https://blog.paperspace.com/rss/",                                                "news"),
    ("PetaPixel",                            "https://petapixel.com/feed",                                                      "news"),
    ("philschmid blog",                      "https://www.philschmid.de/feed.xml",                                             "news"),
    ("Max Woolf's Blog",                     "https://minimaxir.com/post/index.xml",                                            "news"),
    ("Product Hunt",                         "https://www.producthunt.com/feed",                                                "news"),
    ("Python Insider",                       "https://feeds.feedburner.com/PythonInsider",                                     "news"),
    ("Quanta Magazine",                      "https://api.quantamagazine.org/feed",                                             "news"),
    ("Radix – Medium",                       "https://medium.com/feed/radix-ai-blog",                                          "news"),
    ("R-bloggers",                           "https://feeds.feedburner.com/RBloggers",                                          "news"),
    ("Replicate Blog",                       "https://replicate.com/blog/rss",                                                  "news"),
    ("Replicate Codex",                      "https://notes.replicatecodex.com/rss/",                                           "news"),
    ("Rest of World – Latest Stories",       "https://restofworld.org/feed/latest",                                            "news"),
    ("Robotics Research News – ScienceDaily","https://www.sciencedaily.com/rss/computers_math/robotics.xml",                  "news"),
    ("Robotics – Tech.eu",                   "https://tech.eu/category/robotics/feed",                                         "news"),
    ("Scientific American",                  "http://rss.sciam.com/ScientificAmerican-Global",                                 "news"),
    ("SemiAnalysis",                         "https://www.semianalysis.com/feed",                                               "news"),
    ("Silicon Republic",                     "https://www.siliconrepublic.com/feed",                                            "news"),
    ("Simon Willison's Weblog",              "https://simonwillison.net/atom/everything/",                                     "news"),
    ("Stack Overflow Blog",                  "https://stackoverflow.blog/feed/",                                                "news"),
    ("Stanford CRFM",                        "https://crfm.stanford.edu/feed",                                                  "news"),
    ("stat.ML updates on arXiv.org",         "https://arxiv.org/rss/stat.ML",                                                   "news"),
    ("Netflix Technology Blog – Medium",     "https://medium.com/feed/@netflixtechblog",                                       "news"),
    ("ODSC – Medium",                        "https://medium.com/feed/@odsc",                                                   "news"),
    ("Synced",                               "https://syncedreview.com/feed",                                                   "news"),
    ("Synthedia",                            "https://synthedia.substack.com/feed",                                             "news"),
    ("TechCrunch",                           "https://techcrunch.com/feed/",                                                    "news"),
    ("Techmeme",                             "https://www.techmeme.com/feed.xml",                                               "news"),
    ("Tech Monitor",                         "https://techmonitor.ai/feed",                                                     "news"),
    ("Technology Archives – Reuters",        "https://www.reutersagency.com/feed/?best-topics=tech",                           "news"),
    ("TechSpot",                             "https://www.techspot.com/backend.xml",                                            "news"),
    ("TechTalks",                            "https://bdtechtalks.com/feed/",                                                   "news"),
    ("The Algorithmic Bridge",               "https://thealgorithmicbridge.substack.com/feed",                                 "news"),
    ("The Berkeley AI Research Blog",        "https://bair.berkeley.edu/blog/feed.xml",                                        "news"),
    ("THE DECODER",                          "https://the-decoder.com/feed/",                                                   "news"),
    ("The Gradient",                         "https://thegradient.pub/rss/",                                                    "news"),
    ("The Information",                      "https://www.theinformation.com/feed",                                             "news"),
    ("The Intrinsic Perspective",            "https://www.theintrinsicperspective.com/feed/",                                   "news"),
    ("The New Stack",                        "https://thenewstack.io/feed",                                                     "news"),
    ("The Next Web (Neural)",                "https://thenextweb.com/neural/feed",                                              "news"),
    ("The Register – AI",                    "https://www.theregister.com/software/ai_ml/headlines.atom",                     "news"),
    ("The Rundown AI",                       "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                                   "news"),
    ("TheSequence",                          "https://thesequence.substack.com/feed",                                           "news"),
    ("The Stack",                            "https://www.thestack.technology/latest/rss/",                                     "news"),
    ("The TensorFlow Blog",                  "https://blog.tensorflow.org/feeds/posts/default?alt=rss",                       "news"),
    ("The Verge – All Posts",                "https://www.theverge.com/rss/index.xml",                                         "news"),
    ("Towards AI – Medium",                  "https://pub.towardsai.net/feed",                                                  "news"),
    ("Towards Data Science – Medium",        "https://towardsdatascience.com/feed",                                             "news"),
    ("Unite.AI",                             "https://www.unite.ai/feed/",                                                      "news"),
    ("Unwind AI",                            "https://unwindai.substack.com/feed",                                              "news"),
    ("Visual Studio Magazine",               "https://visualstudiomagazine.com/rss-feeds/news.aspx",                           "news"),
    ("Voicebot.ai",                          "https://voicebot.ai/feed/",                                                       "news"),
    ("Weights & Biases: Fully Connected",    "https://wandb.ai/fully-connected/rss.xml",                                       "news"),
    ("Windows Blog",                         "https://blogs.windows.com/feed",                                                  "news"),
    ("Wolfram Blog",                         "https://blog.wolfram.com/feed/",                                                  "news"),
    ("AIhub",                                "https://aihub.org/feed?cat=-473",                                                 "news"),
]

GITHUB_PODCAST_FEEDS = [
    ("Adventures in Machine Learning",       "https://topenddevs.com/podcasts/adventures-in-machine-learning/rss.rss",         "podcast"),
    ("AI in Financial Services Podcast",     "https://aiandbanking.libsyn.com/rss",                                            "podcast"),
    ("AI Today Podcast",                     "https://feeds.blubrry.com/feeds/aitoday.xml",                                    "podcast"),
    ("Babbage from The Economist",           "https://feeds.acast.com/public/shows/e421d786-ec36-4148-aa99-7a3b2928a779",      "podcast"),
    ("Data Engineering Podcast",             "https://www.dataengineeringpodcast.com/feed/mp3/",                               "podcast"),
    ("Data Science at Home",                 "https://datascienceathome.com/feed.xml",                                         "podcast"),
    ("Data Skeptic",                         "https://dataskeptic.libsyn.com/rss",                                             "podcast"),
    ("Data Stories",                         "https://datastori.es/feed/",                                                      "podcast"),
    ("DataTalks.Club",                       "https://anchor.fm/s/41286f68/podcast/rss",                                       "podcast"),
    ("The ChatGPT Report",                   "https://www.thechatgptreport.com/episodes?format=rss",                           "podcast"),
    ("Eye On A.I.",                          "https://aneyeonai.libsyn.com/rss",                                                "podcast"),
    ("Geomob",                               "https://geomob-podcast.castos.com/feed",                                         "podcast"),
    ("Global AI Podcast",                    "https://anchor.fm/s/443868ac/podcast/rss",                                       "podcast"),
    ("Gradient Dissent",                     "https://feeds.captivate.fm/gradient-dissent/",                                   "podcast"),
    ("Harvard Data Science Review Podcast",  "https://feed.podbean.com/hdsr/feed.xml",                                         "podcast"),
    ("MLOps.community",                      "https://anchor.fm/s/174cb1b8/podcast/rss",                                       "podcast"),
    ("NLP Highlights",                       "http://feeds.soundcloud.com/users/soundcloud:users:306749289/sounds.rss",        "podcast"),
    ("Not So Standard Deviations",           "http://nssdeviations.com/rss",                                                   "podcast"),
    ("Postgres FM",                          "https://feeds.transistor.fm/postgres-fm",                                        "podcast"),
    ("Practical AI",                         "https://changelog.com/practicalai/feed",                                         "podcast"),
    ("Small Data Forum Podcast",             "http://lexisnexisbis.libsyn.com/rss",                                            "podcast"),
    ("Talk Python To Me",                    "https://talkpython.fm/episodes/rss",                                             "podcast"),
    ("The AI Breakdown",                     "https://feeds.libsyn.com/468519/rss",                                            "podcast"),
    ("The AI in Business Podcast",           "http://podcast.emerj.com/rss",                                                   "podcast"),
    ("The AI Podcast (NVIDIA)",              "http://feeds.soundcloud.com/users/soundcloud:users:264034133/sounds.rss",        "podcast"),
    ("The Artificial Intelligence Podcast",  "https://anchor.fm/s/3952c6f8/podcast/rss",                                      "podcast"),
    ("The Artists of Data Science",          "https://feeds.fireside.fm/theartistsofdatascience/rss",                         "podcast"),
    ("The Data Engineering Show",            "https://feeds.transistor.fm/the-data-engineering-show",                         "podcast"),
    ("The Data Exchange",                    "https://thedataexchange.media/feed/",                                            "podcast"),
    ("The Gradient Podcast",                 "https://api.substack.com/feed/podcast/265424/s/1354.rss",                       "podcast"),
    ("The Machine Learning Podcast",         "https://www.themachinelearningpodcast.com/rss",                                  "podcast"),
    ("The Marketing AI Show",                "https://feeds.megaphone.fm/marketingai",                                         "podcast"),
    ("The TWIML AI Podcast",                 "https://twimlai.com/feed",                                                       "podcast"),
    ("This Day in AI Podcast",               "https://feeds.transistor.fm/this-day-in-ai",                                    "podcast"),
    ("Utilizing Tech Season 5",              "https://anchor.fm/s/32ec7408/podcast/rss",                                       "podcast"),
]

GITHUB_VIDEO_FEEDS = [
    ("1littlecoder (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCpV_X0VrL8-jg3t6wYGS-1g",  "video"),
    ("Abhishek Thakur (YT)",                 "https://www.youtube.com/feeds/videos.xml?channel_id=UCBPRJjIWfyNG4X-CRbnv78A",  "video"),
    ("AI Coffee Break with Letitia (YT)",    "https://www.youtube.com/feeds/videos.xml?channel_id=UCobqgqE4i5Kf7wrxRxhToQA", "video"),
    ("AI Explained (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw",  "video"),
    ("AI Jason (YT)",                        "https://www.youtube.com/feeds/videos.xml?channel_id=UCrXSVX9a1mj8l0CMLwKgMVw",  "video"),
    ("Aitrepreneur (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCEAbqW0HFB_UxZoUDO0kJBw",  "video"),
    ("Aleksa Gordic – The AI Epiphany (YT)", "https://www.youtube.com/feeds/videos.xml?channel_id=UCj8shE7aIn4Yawwbo2FceCQ", "video"),
    ("Alex The Analyst (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UC7cs8q-gJRlGwj4A8OmCmXg",  "video"),
    ("All About AI (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCR9j1jqqB5Rse69wjUnbYwA",  "video"),
    ("Allen Institute for AI (YT)",          "https://www.youtube.com/feeds/videos.xml?channel_id=UCEqgmyWChwvt6MFGGlmUQCQ", "video"),
    ("Analytics India Magazine (YT)",        "https://www.youtube.com/feeds/videos.xml?channel_id=UCAlwrsgeJavG1vw9qSFOUmA", "video"),
    ("Anastasi In Tech (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCORX3Cl7ByidjEgzSCgv9Yw", "video"),
    ("Andrej Baranovskij (YT)",              "https://www.youtube.com/feeds/videos.xml?channel_id=UCqSX0Z20QCEE7tZKaQ4pS3Q", "video"),
    ("AssemblyAI (YT)",                      "https://www.youtube.com/feeds/videos.xml?channel_id=UCtatfZMf-8EkIwASXM4ts0A", "video"),
    ("Avra (YT)",                            "https://www.youtube.com/feeds/videos.xml?channel_id=UCDMP6ATYKNXMvn2ok1gfM7Q", "video"),
    ("code_your_own_AI (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCfOvNb3xj28SNqPQ_JIbumg", "video"),
    ("Data Independent (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCyR2Ct3pDOeZSRyZH5hPO-Q", "video"),
    ("David Shapiro ~ AI (YT)",              "https://www.youtube.com/feeds/videos.xml?channel_id=UCvKRFNawVcuz4b9ihUTApCg", "video"),
    ("DeepMind (YT)",                        "https://www.youtube.com/feeds/videos.xml?channel_id=UCP7jMXSY2xbc3KCAE0MHQ-A", "video"),
    ("Edan Meyer (YT)",                      "https://www.youtube.com/feeds/videos.xml?channel_id=UC66Ggxy8MHX9DCDohdRYDTA", "video"),
    ("Full Stack Deep Learning (YT)",        "https://www.youtube.com/feeds/videos.xml?channel_id=UCVchfoB65aVtQiDITbGq2LQ", "video"),
    ("H2O.ai (YT)",                          "https://www.youtube.com/feeds/videos.xml?channel_id=UCk6ONJlPzjw3DohAeMSgsng", "video"),
    ("IBM Research (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCwx7Y3W30N8aS_tiCy2x-2g", "video"),
    ("James Briggs (YT)",                    "https://www.youtube.com/feeds/videos.xml?channel_id=UCv83tO5cePwHMt1952IVVHw", "video"),
    ("Jeremy Howard (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UCX7Y2qWriXpqocG97SFW2OQ", "video"),
    ("Joma Tech (YT)",                       "https://www.youtube.com/feeds/videos.xml?channel_id=UCV0qA-eDDICsRR9rPcnG7tw", "video"),
    ("Jordan Harrod (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UC1H1NWNTG2Xi3pt85ykVSHA", "video"),
    ("Kaggle (YT)",                          "https://www.youtube.com/feeds/videos.xml?channel_id=UCSNeZleDn9c74yQc-EKnVTA", "video"),
    ("Keith Galli (YT)",                     "https://www.youtube.com/feeds/videos.xml?channel_id=UCq6XkhO5SZ66N04IcPbqNcw", "video"),
    ("Ken Jee (YT)",                         "https://www.youtube.com/feeds/videos.xml?channel_id=UCiT9RITQ9PW6BhXK0y2jaeg", "video"),
    ("LlamaIndex (YT)",                      "https://www.youtube.com/feeds/videos.xml?channel_id=UCeRjipR4_SsCddq9VZ2AeKg", "video"),
    ("Machine Learning Street Talk (YT)",    "https://www.youtube.com/feeds/videos.xml?channel_id=UCMLtBahI5DMrt0NPvDSoIRQ", "video"),
    ("Manning Publications (YT)",            "https://www.youtube.com/feeds/videos.xml?channel_id=UCDia_lkNYKLJVRLQl_-pFw",  "video"),
    ("Martin Thissen (YT)",                  "https://www.youtube.com/feeds/videos.xml?channel_id=UCXx0JWOKERPZdzczPfY-huA", "video"),
    ("Matt Wolfe (YT)",                      "https://www.youtube.com/feeds/videos.xml?channel_id=UChpleBmo18P08aKCIgti38g", "video"),
    ("MLOps.community (YT)",                 "https://www.youtube.com/feeds/videos.xml?channel_id=UCG6qpjVnBTTT8wLGBygANOQ", "video"),
    ("Nicholas Renotte (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCHXa4OpASJEwrHrLeIzw7Yg", "video"),
    ("NVIDIA (YT)",                          "https://www.youtube.com/feeds/videos.xml?channel_id=UCHuiy8bXnmK5nisYHUd1J5g", "video"),
    ("Olivio Sarikas (YT)",                  "https://www.youtube.com/feeds/videos.xml?channel_id=UCCKx8mAHiFus-XYQLy_WnaA", "video"),
    ("Patrick Loeber (YT)",                  "https://www.youtube.com/feeds/videos.xml?channel_id=UCbXgNpp0jedKWcQiULLbDTA", "video"),
    ("Playground AI (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UCUbLzJ30GLE1F5OSWNoYs9g", "video"),
    ("Prompt Engineering (YT)",              "https://www.youtube.com/feeds/videos.xml?channel_id=UCDq7SjbgRKty5TgGafW8Clg", "video"),
    ("Rabbitmetrics (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UCNszHNG0PlhWJdtNqFvwMWw", "video"),
    ("Reuven Lerner (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UCBqMxo5ch1NN0hZsM58gf6Q", "video"),
    ("Sam Witteveen (YT)",                   "https://www.youtube.com/feeds/videos.xml?channel_id=UC55ODQSvARtgSyc8ThfiepQ", "video"),
    ("sentdex (YT)",                         "https://www.youtube.com/feeds/videos.xml?channel_id=UCfzlCWGWYyIQ0aLC5w48gBQ", "video"),
    ("Super Data Science Podcast (YT)",      "https://www.youtube.com/feeds/videos.xml?channel_id=UCMbtqTGdSsxYYhhTpV4lSTQ", "video"),
    ("TensorFlow (YT)",                      "https://www.youtube.com/feeds/videos.xml?channel_id=UC0rqucBdTuFTjJiefW5t-IQ", "video"),
    ("The AI Advantage (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCHhYXsLBEVVnbvsq57n1MTQ", "video"),
    ("The Data Scientist Show (YT)",         "https://www.youtube.com/feeds/videos.xml?channel_id=UCa0RTSXWyZdh7IciV9r-3ow", "video"),
    ("Thu Vu data analytics (YT)",           "https://www.youtube.com/feeds/videos.xml?channel_id=UCJQJAI7IjbLcpsjWdSzYz0Q", "video"),
    ("Towards Data Science (YT)",            "https://www.youtube.com/feeds/videos.xml?channel_id=UCuHZ1UYfHRqk3-5N5oc97Kw", "video"),
    ("Two Minute Papers (YT)",               "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg", "video"),
    ("Unconventional Coding (YT)",           "https://www.youtube.com/feeds/videos.xml?channel_id=UCqp4QHWfVYd65onoyraiYvg", "video"),
    ("Venelin Valkov (YT)",                  "https://www.youtube.com/feeds/videos.xml?channel_id=UCoW_WzQNJVAjxo4osNAxd_g", "video"),
    ("Weights & Biases (YT)",                "https://www.youtube.com/feeds/videos.xml?channel_id=UCBp3w4DCEC64FZr4k9ROxig",  "video"),
    ("What's AI by Louis Bouchard (YT)",     "https://www.youtube.com/feeds/videos.xml?channel_id=UCUzGQrN-lyyc0BWTYoJM_Sg", "video"),
    ("Wolfram (YT)",                         "https://www.youtube.com/feeds/videos.xml?channel_id=UCJekgf6k62CQHdENWf2NgAQ", "video"),
    ("WorldofAI (YT)",                       "https://www.youtube.com/feeds/videos.xml?channel_id=UC2WmuBuFq6gL08QYG-JjXKw", "video"),
    ("Yannic Kilcher (YT)",                  "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew", "video"),
]

GITHUB_JOBS_FEEDS = [
    ("aijobs.net",                           "https://aijobs.net/feed/",                                                       "jobs"),
]

# ── Existing feeds from feeds.py ──────────────────────────────────────────────

EXISTING_FEEDS = [
    ("OpenAI Blog",            "https://openai.com/news/rss.xml",                                              "ai-updates"),
    ("Google DeepMind",        "https://deepmind.google/blog/rss.xml",                                        "ai-updates"),
    ("Google Blog AI",         "https://blog.google/technology/ai/rss/",                                      "ai-updates"),
    ("Google Research",        "https://research.google/blog/rss/",                                           "ai-updates"),
    ("Microsoft AI",           "https://blogs.microsoft.com/ai/feed",                                         "ai-updates"),
    ("Apple ML",               "https://machinelearning.apple.com/rss.xml",                                   "ai-updates"),
    ("NVIDIA Blog",            "https://feeds.feedburner.com/nvidiablog",                                     "ai-updates"),
    ("MIT AI News",            "https://news.mit.edu/rss/topic/artificial-intelligence2",                     "ai-updates"),
    ("Berkeley AI (BAIR)",     "https://bair.berkeley.edu/blog/feed.xml",                                     "ai-updates"),
    ("CMU ML Blog",            "https://blog.ml.cmu.edu/feed",                                                "ai-updates"),
    ("AI News",                "https://www.artificialintelligence-news.com/feed/",                           "ai-updates"),
    ("The Verge AI",           "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",          "ai-updates"),
    ("The Verge Tech",         "https://www.theverge.com/rss/tech/index.xml",                                "ai-updates"),
    ("Ars Technica",           "https://feeds.arstechnica.com/arstechnica/index",                            "ai-updates"),
    ("MIT Tech Review AI",     "https://www.technologyreview.com/topic/artificial-intelligence/feed/",       "ai-updates"),
    ("MIT Tech Review",        "https://www.technologyreview.com/feed/",                                      "ai-updates"),
    ("MarkTechPost",           "https://www.marktechpost.com/feed/",                                         "ai-updates"),
    ("Import AI (Jack Clark)", "https://importai.substack.com/feed",                                         "ai-updates"),
    ("Import AI (Beehiiv)",    "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                              "ai-updates"),
    ("arXiv cs.AI",            "https://rss.arxiv.org/rss/cs.AI",                                           "ai-updates"),
    ("arXiv cs.CL (NLP)",      "https://arxiv.org/rss/cs.CL",                                               "ai-updates"),
    ("TechCrunch AI",          "https://techcrunch.com/category/artificial-intelligence/feed/",              "ai-business"),
    ("TechCrunch (main)",      "https://techcrunch.com/feed/",                                               "ai-business"),
    ("VentureBeat",            "https://venturebeat.com/category/ai/feed/",                                  "ai-business"),
    ("Reuters via Google News","https://news.google.com/rss/search?q=site%3Areuters.com+technology&hl=en-US&gl=US&ceid=US%3Aen", "ai-business"),
    ("NYT Technology",         "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",               "ai-business"),
    ("CNBC Tech",              "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910", "ai-business"),
    ("WSJ Tech",               "https://feeds.content.dowjones.io/public/rss/RSSWSJD",                      "ai-business"),
    ("Meta News",              "https://about.fb.com/feed",                                                  "ai-business"),
    ("Databricks Blog",        "https://www.databricks.com/feed",                                            "ai-business"),
    ("Hugging Face Blog",      "https://huggingface.co/blog/feed.xml",                                      "ai-dev"),
    ("Towards Data Science",   "https://towardsdatascience.com/feed",                                        "ai-dev"),
    ("NVIDIA Developer",       "https://developer.nvidia.com/blog/feed",                                     "ai-dev"),
    ("AWS Machine Learning",   "https://aws.amazon.com/blogs/machine-learning/feed/",                       "ai-dev"),
    ("AWS DevOps",             "https://aws.amazon.com/blogs/devops/feed/",                                  "ai-dev"),
    ("Meta Engineering",       "https://engineering.fb.com/feed",                                            "ai-dev"),
    ("Nanonets Blog",          "https://nanonets.com/blog/rss",                                              "ai-dev"),
    ("Kubernetes Blog",        "https://kubernetes.io/feed.xml",                                             "ai-dev"),
    ("HashiCorp Blog",         "https://www.hashicorp.com/blog/feed.xml",                                   "ai-dev"),
    ("Databricks Docs",        "https://docs.databricks.com/aws/en/feed.xml",                               "ai-dev"),
    ("arXiv cs.LG (ML)",       "https://arxiv.org/rss/cs.LG",                                               "ai-dev"),
    ("arXiv stat.ML",          "https://arxiv.org/rss/stat.ML",                                             "ai-dev"),
    ("Product Hunt",           "https://www.producthunt.com/feed",                                           "ai-dev"),
    ("ByteByteGo",             "https://blog.bytebytego.com/feed",                                          "ai-dev"),
    ("Hacker News Front Page", "https://hnrss.org/frontpage",                                                "ai-dev"),
    ("The Hacker News",        "https://feeds.feedburner.com/TheHackersNews",                               "security"),
    ("Krebs on Security",      "https://krebsonsecurity.com/feed/",                                          "security"),
    ("Dark Reading",           "https://www.darkreading.com/rss.xml",                                        "security"),
    ("Palo Alto Unit 42",      "https://unit42.paloaltonetworks.com/feed/",                                  "security"),
    ("Threatpost",             "https://threatpost.com/feed/",                                               "security"),
    ("Infosecurity Magazine",  "https://www.infosecurity-magazine.com/rss/news/",                           "security"),
    ("Microsoft Security",     "https://api.msrc.microsoft.com/update-guide/rss",                           "security"),
    ("The Verge Security",     "https://www.theverge.com/rss/cyber-security/index.xml",                    "security"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication: lowercase, strip trailing slash."""
    url = url.strip().rstrip("/")
    # strip query string variations that are just formatting flags
    if "?format=rss" in url or "?format=xml" in url:
        url = url.split("?")[0]
    return url.lower()


def check_url(url: str, timeout: int = 10) -> tuple[bool, int, str]:
    """
    Return (is_valid, http_status, error_note).
    Follows up to 5 redirects. Treats 2xx/3xx as valid.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FeedChecker/1.0)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return True, resp.status, ""
    except urllib.error.HTTPError as e:
        if e.code in (405, 406):
            # HEAD not allowed — try GET
            try:
                req2 = urllib.request.Request(url, headers=headers, method="GET")
                resp2 = urllib.request.urlopen(req2, timeout=timeout)
                return True, resp2.status, ""
            except Exception as e2:
                return False, 0, str(e2)[:80]
        return False, e.code, e.reason[:80] if e.reason else ""
    except Exception as e:
        return False, 0, str(e)[:80]


def build_candidates() -> list[dict]:
    """Combine feedspot + github feeds, deduplicate by normalized URL."""
    all_feeds: list[tuple[str, str, str, str]] = []  # (name, url, category, source)

    for name, url, cat in FEEDSPOT_FEEDS:
        all_feeds.append((name, url, cat, "feedspot"))
    for name, url, cat in GITHUB_NEWS_FEEDS:
        all_feeds.append((name, url, cat, "github"))
    for name, url, cat in GITHUB_PODCAST_FEEDS:
        all_feeds.append((name, url, cat, "github"))
    for name, url, cat in GITHUB_VIDEO_FEEDS:
        all_feeds.append((name, url, cat, "github"))
    for name, url, cat in GITHUB_JOBS_FEEDS:
        all_feeds.append((name, url, cat, "github"))

    seen: dict[str, dict] = {}
    for name, url, cat, source in all_feeds:
        key = normalize_url(url)
        if key in seen:
            # merge sources
            existing_sources = seen[key]["sources"].split("+")
            if source not in existing_sources:
                seen[key]["sources"] = "+".join(existing_sources + [source])
        else:
            seen[key] = {
                "name": name,
                "url": url,
                "category": cat,
                "sources": source,
                "valid": "",
                "http_status": "",
                "error": "",
            }

    return list(seen.values())


def validate_all(candidates: list[dict], workers: int = 20) -> None:
    """Fill in valid/http_status/error fields in-place, with progress."""
    total = len(candidates)
    done = 0

    def task(item):
        valid, status, error = check_url(item["url"])
        return item, valid, status, error

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(task, c): c for c in candidates}
        for fut in as_completed(futures):
            item, valid, status, error = fut.result()
            item["valid"] = "YES" if valid else "NO"
            item["http_status"] = status
            item["error"] = error
            done += 1
            if done % 25 == 0 or done == total:
                print(f"  Checked {done}/{total}...", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    candidates_path = os.path.join(data_dir, "new_feeds_candidates.csv")
    final_path      = os.path.join(data_dir, "feed_status.csv")

    # ── Step 1: build + validate candidates ───────────────────────────────────
    print(f"Building candidate list from feedspot + github...")
    candidates = build_candidates()
    print(f"  {len(candidates)} unique URLs after dedup")

    print("Validating feeds (HEAD/GET requests, 20 workers)...")
    validate_all(candidates)

    valid_count = sum(1 for c in candidates if c["valid"] == "YES")
    print(f"  {valid_count}/{len(candidates)} feeds responded OK")

    with open(candidates_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "category", "sources", "valid", "http_status", "error"])
        writer.writeheader()
        writer.writerows(sorted(candidates, key=lambda x: (x["category"], x["name"].lower())))
    print(f"Saved: {candidates_path}")

    # ── Step 2: build existing feed_status from feeds.py ──────────────────────
    existing_urls_norm = {normalize_url(url): (name, url, sector)
                          for name, url, sector in EXISTING_FEEDS}

    # ── Step 3: build final CSV ────────────────────────────────────────────────
    # Existing feeds go in first (all of them, no filtering)
    final_rows: list[dict] = []
    for name, url, sector in EXISTING_FEEDS:
        final_rows.append({
            "name": name,
            "url": url,
            "sector": sector,
            "category": "news",
            "source_list": "feeds.py",
            "valid": "",       # not re-checked here
            "http_status": "",
            "notes": "",
        })

    # New candidates that are valid AND not already in existing feeds
    new_added = 0
    for c in candidates:
        if c["valid"] != "YES":
            continue
        key = normalize_url(c["url"])
        if key in existing_urls_norm:
            continue
        # Only include news feeds (skip podcasts, videos, jobs for the newsletter)
        if c["category"] != "news":
            continue
        final_rows.append({
            "name": c["name"],
            "url": c["url"],
            "sector": "",          # to be assigned manually
            "category": c["category"],
            "source_list": c["sources"],
            "valid": c["valid"],
            "http_status": c["http_status"],
            "notes": "NEW — assign sector",
        })
        new_added += 1

    with open(final_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "sector", "category", "source_list", "valid", "http_status", "notes"])
        writer.writeheader()
        writer.writerows(final_rows)

    print(f"Saved: {final_path}")
    print(f"  {len(EXISTING_FEEDS)} existing + {new_added} new valid news feeds = {len(final_rows)} total rows")
    print("\nDone.")


if __name__ == "__main__":
    main()
