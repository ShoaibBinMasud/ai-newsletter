# All RSS feed sources, organized by sector.
# Each entry: (name, url, sector)
# Sector values: "ai-updates" | "ai-business" | "ai-dev" | "security"
#
# Source column:
#   feeds.py  = original curated feed
#   feedspot  = from rss.feedspot.com/ai_rss_feeds/
#   github    = from github.com/foorilla/allainews_sources
#   feedspot+github = appeared in both sources

FEEDS = [
    # ── AI Updates: model releases, research, product launches ────────────────
    ("OpenAI Blog",                                    "https://openai.com/news/rss.xml",                                                         "ai-updates"),  
    ("Google DeepMind",                                "https://deepmind.google/blog/rss.xml",                                                    "ai-updates"),  
    ("Google Blog AI",                                 "https://blog.google/technology/ai/rss/",                                                  "ai-updates"),  
    ("Google Research",                                "https://research.google/blog/rss/",                                                       "ai-updates"),  
    ("Microsoft AI",                                   "https://blogs.microsoft.com/ai/feed",                                                     "ai-updates"),  
    ("Apple ML",                                       "https://machinelearning.apple.com/rss.xml",                                               "ai-updates"),  
    ("NVIDIA Blog",                                    "https://feeds.feedburner.com/nvidiablog",                                                 "ai-updates"),  
    ("MIT AI News",                                    "https://news.mit.edu/rss/topic/artificial-intelligence2",                                 "ai-updates"),  
    ("Berkeley AI (BAIR)",                             "https://bair.berkeley.edu/blog/feed.xml",                                                 "ai-updates"),  
    ("CMU ML Blog",                                    "https://blog.ml.cmu.edu/feed",                                                            "ai-updates"),  
    ("AI News",                                        "https://www.artificialintelligence-news.com/feed/",                                       "ai-updates"),  
    ("The Verge AI",                                   "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",                       "ai-updates"),  
    ("The Verge Tech",                                 "https://www.theverge.com/rss/tech/index.xml",                                             "ai-updates"),  
    ("Ars Technica",                                   "https://feeds.arstechnica.com/arstechnica/index",                                         "ai-updates"),  
    ("MIT Tech Review AI",                             "https://www.technologyreview.com/topic/artificial-intelligence/feed/",                    "ai-updates"),  
    ("MIT Tech Review",                                "https://www.technologyreview.com/feed/",                                                  "ai-updates"),  
    ("MarkTechPost",                                   "https://www.marktechpost.com/feed/",                                                      "ai-updates"),  
    ("Import AI (Jack Clark)",                         "https://importai.substack.com/feed",                                                      "ai-updates"),  
    ("Import AI (Beehiiv)",                            "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",                                            "ai-updates"),  
    ("arXiv cs.AI",                                    "https://rss.arxiv.org/rss/cs.AI",                                                         "ai-updates"),  
    ("arXiv cs.CL (NLP)",                              "https://arxiv.org/rss/cs.CL",                                                             "ai-updates"),  
    ("404 Media",                                      "https://www.404media.co/rss",                                                             "ai-updates"),    # github
    ("Ahead of AI",                                    "https://magazine.sebastianraschka.com/feed",                                              "ai-updates"),    # github
    ("AI 2 People",                                    "https://ai2people.com/feed/",                                                             "ai-updates"),    # feedspot
    ("AI Accelerator Institute",                       "https://aiacceleratorinstitute.com/rss/",                                                 "ai-updates"),    # github
    ("AI for Good Blog",                               "https://aiforgood.itu.int/feed/",                                                         "ai-updates"),    # feedspot
    ("AI Insider",                                     "https://theaiinsider.tech/feed/",                                                         "ai-updates"),    # feedspot
    ("AI nyheter (aitool.se)",                         "https://nyheter.aitool.se/feed/",                                                         "ai-updates"),    # feedspot
    ("AI Revolution Blog",                             "https://airevolution.blog/feed/",                                                         "ai-updates"),    # feedspot
    ("AI Snake Oil",                                   "https://aisnakeoil.substack.com/feed",                                                    "ai-updates"),    # github
    ("AI Summer",                                      "https://theaisummer.com/feed.xml",                                                        "ai-updates"),    # feedspot
    ("AI Time Journal",                                "https://www.aitimejournal.com/feed/",                                                     "ai-updates"),    # feedspot
    ("AI Weekly",                                      "https://aiweekly.co/issues.rss",                                                          "ai-updates"),    # feedspot
    ("AI – SiliconANGLE",                              "https://siliconangle.com/category/ai/feed",                                               "ai-updates"),    # github
    ("AICorr.com",                                     "https://aicorr.com/feed/",                                                                "ai-updates"),    # feedspot
    ("AIhub",                                          "https://aihub.org/feed/?cat=-473",                                                        "ai-updates"),    # feedspot
    ("AIhub",                                          "https://aihub.org/feed?cat=-473",                                                         "ai-updates"),    # github
    ("AIIOT Talk",                                     "https://www.aiiottalk.com/feed/",                                                         "ai-updates"),    # feedspot
    ("AIModels.fyi",                                   "https://aimodels.substack.com/feed",                                                      "ai-updates"),    # github
    ("AIwire",                                         "https://www.aiwire.net/feed/",                                                            "ai-updates"),    # feedspot
    ("Anaconda Blog",                                  "https://www.anaconda.com/blog/feed",                                                      "ai-updates"),    # github
    ("Analytics India Magazine",                       "https://analyticsindiamag.com/feed/",                                                     "ai-updates"),    # github
    ("Analytics India Magazine - AI News",             "https://analyticsindiamag.com/ai-news-updates/feed/",                                     "ai-updates"),    # feedspot
    ("Another Datum",                                  "https://anotherdatum.com/feeds/all.atom.xml?format=xml",                                  "ai-updates"),    # feedspot
    ("Archie.AI (Medium)",                             "https://medium.com/feed/archieai",                                                        "ai-updates"),    # feedspot
    ("Ars Technica - AI",                              "https://arstechnica.com/ai/feed/",                                                        "ai-updates"),    # feedspot
    ("Artificial Intelligence – Futurism",             "https://futurism.com/categories/ai-artificial-intelligence/feed",                         "ai-updates"),    # github
    ("Artificial intelligence – SpaceNews",            "https://spacenews.com/tag/artificial-intelligence/feed/",                                 "ai-updates"),    # github
    ("Artificial Intelligence – TechRepublic",         "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/",                    "ai-updates"),    # github
    ("Artificial intelligence – The Conversation (EU)", "https://theconversation.com/europe/topics/artificial-intelligence-ai-90/articles.atom",   "ai-updates"),    # github
    ("Artificial-Intelligence.Blog",                   "https://www.artificial-intelligence.blog/ai-news?format=rss",                             "ai-updates"),    # feedspot
    ("Artisse AI Blog",                                "https://artisse.ai/feed/",                                                                "ai-updates"),    # feedspot
    ("AWS News Blog - AI",                             "https://aws.amazon.com/blogs/aws/category/artificial-intelligence/feed/",                 "ai-updates"),    # feedspot
    ("Becoming Human",                                 "https://becominghuman.ai/feed",                                                           "ai-updates"),    # feedspot
    ("Berkshire Grey Blog",                            "https://www.berkshiregrey.com/feed/",                                                     "ai-updates"),    # feedspot
    ("Big Data – SiliconANGLE",                        "https://siliconangle.com/category/big-data/feed",                                         "ai-updates"),    # github
    ("Chain of Thought (every.to)",                    "https://every.to/chain-of-thought/feed.xml",                                              "ai-updates"),    # github
    ("Cisco Blogs - AI",                               "https://blogs.cisco.com/ai/feed",                                                         "ai-updates"),    # feedspot
    ("Clarifai Blog",                                  "https://www.clarifai.com/blog/rss.xml",                                                   "ai-updates"),    # feedspot
    ("Cogito Tech Blog",                               "https://www.cogitotech.com/feed/",                                                        "ai-updates"),    # feedspot
    ("Computational Intelligence (Blogspot)",          "http://computational-intelligence.blogspot.com/feeds/posts/default",                      "ai-updates"),    # feedspot
    ("Contextual AI Blog",                             "https://contextual.ai/blog/feed/",                                                        "ai-updates"),    # feedspot
    ("Copyleaks Blog",                                 "https://copyleaks.com/blog/feed",                                                         "ai-updates"),    # feedspot
    ("DailyAI",                                        "https://dailyai.com/feed/",                                                               "ai-updates"),    # feedspot
    ("Dan Rose AI Blog",                               "https://www.danrose.ai/blog?format=rss",                                                  "ai-updates"),    # feedspot
    ("DataRobot Blog",                                 "https://www.datarobot.com/blog/feed/",                                                    "ai-updates"),    # feedspot
    ("DatumBox",                                       "http://blog.datumbox.com/feed/",                                                          "ai-updates"),    # feedspot
    ("DeepCognition.ai Blog",                          "https://deepcognition.ai/feed/",                                                          "ai-updates"),    # feedspot
    ("DeepMind Blog",                                  "https://deepmind.com/blog/feed/basic/",                                                   "ai-updates"),    # github
    ("Department of Product",                          "https://departmentofproduct.substack.com/feed",                                           "ai-updates"),    # github
    ("Digital Thought Disruption",                     "https://digitalthoughtdisruption.com/feed/",                                              "ai-updates"),    # feedspot
    ("DLabs.AI Blog",                                  "https://dlabs.ai/feed/",                                                                  "ai-updates"),    # feedspot
    ("Dxcover Blog",                                   "https://www.dxcover.com/feed/",                                                           "ai-updates"),    # feedspot
    ("EE Times",                                       "https://www.eetimes.com/feed",                                                            "ai-updates"),    # github
    ("ELEDIA E-AIR",                                   "http://www.eledia.org/e-air/feed/",                                                       "ai-updates"),    # feedspot
    ("Engadget",                                       "https://www.engadget.com/rss.xml",                                                        "ai-updates"),    # github
    ("Francesco Corea (Medium)",                       "https://medium.com/feed/@Francesco_AI",                                                   "ai-updates"),    # feedspot
    ("Freethink",                                      "https://www.freethink.com/feed/all",                                                      "ai-updates"),    # github
    ("Fusemachines Insights",                          "https://insights.fusemachines.com/feed/",                                                 "ai-updates"),    # feedspot
    ("Generational",                                   "https://www.generational.pub/feed",                                                       "ai-updates"),    # github
    ("gHacks Technology News",                         "https://www.ghacks.net/feed/",                                                            "ai-updates"),    # github
    ("Gizmodo",                                        "https://gizmodo.com/rss",                                                                 "ai-updates"),    # github
    ("Google AI Blog",                                 "http://googleaiblog.blogspot.com/atom.xml",                                               "ai-updates"),    # github
    ("GPTZero Blog",                                   "https://gptzero.me/news/rss/",                                                            "ai-updates"),    # feedspot
    ("HealthTech Magazine",                            "https://feeds.feedburner.com/HealthTechMagazine",                                         "ai-updates"),    # github
    ("InfoWorld Analytics",                            "https://www.infoworld.com/category/analytics/index.rss",                                  "ai-updates"),    # github
    ("Isentia",                                        "https://www.isentia.com/feed/",                                                           "ai-updates"),    # feedspot
    ("Just AI News",                                   "https://justainews.com/feed/",                                                            "ai-updates"),    # feedspot
    ("Kavita Ganesan",                                 "http://kavita-ganesan.com/feed/",                                                         "ai-updates"),    # feedspot
    ("KocharTech",                                     "https://www.kochartech.com/feed/",                                                        "ai-updates"),    # feedspot
    ("Kore.ai",                                        "https://blog.kore.ai/rss.xml",                                                            "ai-updates"),    # feedspot
    ("Last Week in AI",                                "https://lastweekin.ai/feed",                                                              "ai-updates"),    # github
    ("Live Science - AI",                              "https://www.livescience.com/feeds/tag/artificial-intelligence",                           "ai-updates"),    # feedspot
    ("Machine learning – Nature",                      "https://www.nature.com/subjects/machine-learning.rss",                                    "ai-updates"),    # github
    ("Marek Rosa / GoodAI Blog",                       "https://blog.marekrosa.org/feed/",                                                        "ai-updates"),    # feedspot
    ("MIRI Blog",                                      "https://intelligence.org/feed/",                                                          "ai-updates"),    # feedspot
    ("MIT News – Machine Learning",                    "https://news.mit.edu/topic/mitmachine-learning-rss.xml",                                  "ai-updates"),    # github
    ("Mozilla Foundation Blog",                        "https://foundation.mozilla.org/en/blog/rss/",                                             "ai-updates"),    # github
    ("Netflix Technology Blog – Medium",               "https://medium.com/feed/@netflixtechblog",                                                "ai-updates"),    # github
    ("NeuroSYS Blog - AI",                             "https://neurosys.com/blog/category/ai/feed",                                              "ai-updates"),    # feedspot
    ("New Scientist – Technology",                     "https://www.newscientist.com/subject/technology/feed/",                                   "ai-updates"),    # github
    ("News on AI/ML – TechXplore",                     "https://techxplore.com/rss-feed/machine-learning-ai-news/",                               "ai-updates"),    # github
    ("News on AI/ML – TechXplore (phys.org)",          "https://phys.org/rss-feed/technology-news/machine-learning-ai/",                          "ai-updates"),    # github
    ("Neysa Newsroom",                                 "https://neysa.ai/feed/",                                                                  "ai-updates"),    # feedspot
    ("O'Reilly Media - AI & ML",                       "https://www.oreilly.com/radar/topics/ai-ml/feed/index.xml",                               "ai-updates"),    # feedspot
    ("ODSC – Medium",                                  "https://medium.com/feed/@odsc",                                                           "ai-updates"),    # github
    ("One Useful Thing",                               "https://www.oneusefulthing.org/feed",                                                     "ai-updates"),    # github
    ("Pandio Blog",                                    "https://pandio.com/feed/",                                                                "ai-updates"),    # feedspot
    ("PetaPixel",                                      "https://petapixel.com/feed",                                                              "ai-updates"),    # github
    ("Quanta Magazine",                                "https://api.quantamagazine.org/feed",                                                     "ai-updates"),    # github
    ("Qudata",                                         "https://qudata.com/en/news/rss.xml",                                                      "ai-updates"),    # feedspot
    ("Radix – Medium",                                 "https://medium.com/feed/radix-ai-blog",                                                   "ai-updates"),    # github
    ("Robot Writers AI",                               "https://robotwritersai.com/feed/",                                                        "ai-updates"),    # feedspot
    ("Robotics Research News – ScienceDaily",          "https://www.sciencedaily.com/rss/computers_math/robotics.xml",                            "ai-updates"),    # github
    ("RStudio AI Blog",                                "https://blogs.rstudio.com/ai/index.xml",                                                  "ai-updates"),    # feedspot
    ("SAAL",                                           "https://saal.ai/feed/",                                                                   "ai-updates"),    # feedspot
    ("SAS - AI",                                       "https://blogs.sas.com/content/topic/artificial-intelligence/feed/",                       "ai-updates"),    # feedspot
    ("Science News - AI",                              "https://www.sciencenews.org/topic/artificial-intelligence/feed",                          "ai-updates"),    # feedspot
    ("ScienceDaily - AI News",                         "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",             "ai-updates"),    # feedspot+github
    ("Scientific American",                            "http://rss.sciam.com/ScientificAmerican-Global",                                          "ai-updates"),    # github
    ("Shaip Blog",                                     "https://www.shaip.com/feed/",                                                             "ai-updates"),    # feedspot
    ("Spritle Blog",                                   "https://www.spritle.com/blog/feed/",                                                      "ai-updates"),    # feedspot
    ("Synced",                                         "https://syncedreview.com/feed",                                                           "ai-updates"),    # github
    ("Synthedia",                                      "https://synthedia.substack.com/feed",                                                     "ai-updates"),    # github
    ("TechSpective - AI",                              "https://techspective.net/category/technology/artificial-intelligence/feed/",              "ai-updates"),    # feedspot
    ("TechTalks",                                      "https://bdtechtalks.com/feed/",                                                           "ai-updates"),    # github
    ("The Algorithmic Bridge",                         "https://thealgorithmicbridge.substack.com/feed",                                          "ai-updates"),    # github
    ("The Conversation - AI",                          "https://theconversation.com/topics/artificial-intelligence-ai-90/articles.atom",          "ai-updates"),    # feedspot
    ("THE DECODER",                                    "https://the-decoder.com/feed/",                                                           "ai-updates"),    # github
    ("The Gradient",                                   "https://thegradient.pub/rss/",                                                            "ai-updates"),    # github
    ("The Guardian - AI",                              "https://www.theguardian.com/technology/artificialintelligenceai/rss",                     "ai-updates"),    # feedspot+github
    ("The Indian Express - AI",                        "https://indianexpress.com/section/technology/artificial-intelligence/feed/",              "ai-updates"),    # feedspot
    ("The Intrinsic Perspective",                      "https://www.theintrinsicperspective.com/feed/",                                           "ai-updates"),    # github
    ("The New York Times - AI",                        "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/spotlight/artificial-intelligence/rss.xml", "ai-updates"),    # feedspot
    ("The Next Web (Neural)",                          "https://thenextweb.com/neural/feed",                                                      "ai-updates"),    # github
    ("The Register – AI",                              "https://www.theregister.com/software/ai_ml/headlines.atom",                               "ai-updates"),    # github
    ("The Verge – All Posts",                          "https://www.theverge.com/rss/index.xml",                                                  "ai-updates"),    # github
    ("TheSequence",                                    "https://thesequence.substack.com/feed",                                                   "ai-updates"),    # github
    ("Unbabel Blog",                                   "https://unbabel.com/category/blog/feed/",                                                 "ai-updates"),    # feedspot
    ("Unite.AI",                                       "https://www.unite.ai/feed/",                                                              "ai-updates"),    # feedspot+github
    ("Unwind AI",                                      "https://unwindai.substack.com/feed",                                                      "ai-updates"),    # github
    ("Vectra AI Blog",                                 "https://www.vectra.ai/blog/rss.xml",                                                      "ai-updates"),    # feedspot
    ("viAct.ai Blog",                                  "https://www.viact.ai/blog-feed.xml",                                                      "ai-updates"),    # feedspot
    ("Visual Studio Magazine",                         "https://visualstudiomagazine.com/rss-feeds/news.aspx",                                    "ai-updates"),    # github
    ("Voicebot.ai",                                    "https://voicebot.ai/feed/",                                                               "ai-updates"),    # github
    ("Windows Blog",                                   "https://blogs.windows.com/feed",                                                          "ai-updates"),    # github
    ("WIRED - Artificial Intelligence",                "https://www.wired.com/feed/tag/ai/latest/rss",                                            "ai-updates"),    # feedspot+github
    ("Yatter Blog",                                    "https://yatter.in/feed/",                                                                 "ai-updates"),    # feedspot
    ("Yseop Blog",                                     "https://yseop.com/category/blog/feed/",                                                   "ai-updates"),    # feedspot
    ("Zeroth Principles of AI",                        "https://zerothprinciples.substack.com/feed",                                              "ai-updates"),    # feedspot

    # ── AI Business: funding, M&A, enterprise, policy, markets ───────────────
    ("TechCrunch AI",                                  "https://techcrunch.com/category/artificial-intelligence/feed/",                           "ai-business"), 
    ("TechCrunch (main)",                              "https://techcrunch.com/feed/",                                                            "ai-business"), 
    ("VentureBeat",                                    "https://venturebeat.com/category/ai/feed/",                                               "ai-business"), 
    ("Reuters via Google News",                        "https://news.google.com/rss/search?q=site%3Areuters.com+technology&hl=en-US&gl=US&ceid=US%3Aen", "ai-business"), 
    ("NYT Technology",                                 "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",                             "ai-business"), 
    ("CNBC Tech",                                      "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",     "ai-business"), 
    ("WSJ Tech",                                       "https://feeds.content.dowjones.io/public/rss/RSSWSJD",                                    "ai-business"), 
    ("Meta News",                                      "https://about.fb.com/feed",                                                               "ai-business"), 
    ("Databricks Blog",                                "https://www.databricks.com/feed",                                                         "ai-business"), 
    ("1redDrop - AI",                                  "https://1reddrop.com/category/artificial-intelligence/feed/",                             "ai-business"),   # feedspot
    ("Adweek - AI",                                    "https://www.adweek.com/category/artificial-intelligence/feed/",                           "ai-business"),   # feedspot
    ("AI Business",                                    "https://aibusiness.com/rss.xml",                                                          "ai-business"),   # github
    ("AI Now Institute",                               "https://ainowinstitute.org/category/news/feed",                                           "ai-business"),   # github
    ("AI – AI-TechPark",                               "https://ai-techpark.com/category/ai/feed/",                                               "ai-business"),   # github
    ("Artificial Lawyer",                              "https://www.artificiallawyer.com/feed/",                                                  "ai-business"),   # feedspot
    ("Big Data Analytics News - AI",                   "https://bigdataanalyticsnews.com/category/artificial-intelligence/feed/",                 "ai-business"),   # feedspot
    ("Bloomberg Technology",                           "https://feeds.bloomberg.com/technology/news.rss",                                         "ai-business"),   # github
    ("Business Insider",                               "https://feeds.businessinsider.com/custom/all",                                            "ai-business"),   # github
    ("Business Latest (WIRED)",                        "https://www.wired.com/feed/category/business/latest/rss",                                 "ai-business"),   # github
    ("Computerworld - AI",                             "https://www.computerworld.com/artificial-intelligence/feed/",                             "ai-business"),   # feedspot
    ("Crunchbase News",                                "https://news.crunchbase.com/feed",                                                        "ai-business"),   # github
    ("Crunchbase News - AI",                           "https://news.crunchbase.com/sections/ai/feed/",                                           "ai-business"),   # feedspot
    ("Datafloq",                                       "https://datafloq.com/feed/?post_type=post",                                               "ai-business"),   # github
    ("Datanami",                                       "https://www.datanami.com/feed/",                                                          "ai-business"),   # github
    ("Deep Tech – Tech.eu",                            "https://tech.eu/category/deep-tech/feed",                                                 "ai-business"),   # github
    ("Edmonton Journal - AI",                          "https://edmontonjournal.com/tag/artificial-intelligence/feed.xml",                        "ai-business"),   # feedspot
    ("eWeek - AI",                                     "https://www.eweek.com/feed/",                                                             "ai-business"),   # feedspot
    ("Fast Company - AI",                              "https://www.fastcompany.com/section/artificial-intelligence/rss",                         "ai-business"),   # feedspot
    ("Federal News Network - AI",                      "https://federalnewsnetwork.com/category/technology-main/artificial-intelligence/feed/",   "ai-business"),   # feedspot
    ("Financial Times - AI",                           "https://www.ft.com/artificial-intelligence?format=rss",                                   "ai-business"),   # feedspot
    ("Forrester – AI",                                 "https://www.forrester.com/blogs/category/artificial-intelligence-ai/feed",                "ai-business"),   # github
    ("France 24 - AI",                                 "https://www.france24.com/en/tag/artificial-intelligence/rss",                             "ai-business"),   # feedspot
    ("GeekWire - AI",                                  "https://www.geekwire.com/tag/ai/feed/",                                                   "ai-business"),   # feedspot
    ("Global News – AI",                               "https://globalnews.ca/tag/artificial-intelligence/feed",                                  "ai-business"),   # github
    ("Government Technology - AI",                     "https://www.govtech.com/artificial-intelligence.rss",                                     "ai-business"),   # feedspot
    ("IEEE Spectrum – AI",                             "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",                       "ai-business"),   # github
    ("InfoWorld - AI",                                 "https://www.infoworld.com/artificial-intelligence/feed/",                                 "ai-business"),   # feedspot
    ("International Business Times",                   "https://www.ibtimes.com/rss",                                                             "ai-business"),   # github
    ("Latest from Sifted",                             "https://sifted.eu/feed/?post_type=article",                                               "ai-business"),   # github
    ("Marketing AI Institute Blog",                    "https://www.marketingaiinstitute.com/blog/rss.xml",                                       "ai-business"),   # feedspot
    ("Microsoft - AI",                                 "https://news.microsoft.com/source/topics/ai/feed/",                                       "ai-business"),   # feedspot
    ("Microsoft Research",                             "https://www.microsoft.com/en-us/research/feed/",                                          "ai-business"),   # github
    ("Mint - AI",                                      "https://www.livemint.com/rss/AI",                                                         "ai-business"),   # feedspot
    ("Rest of World – Latest Stories",                 "https://restofworld.org/feed/latest",                                                     "ai-business"),   # github
    ("Robotics – Tech.eu",                             "https://tech.eu/category/robotics/feed",                                                  "ai-business"),   # github
    ("Scripps News - AI",                              "https://www.scrippsnews.com/science-and-tech/artificial-intelligence.rss",                "ai-business"),   # feedspot
    ("Silicon Republic",                               "https://www.siliconrepublic.com/feed",                                                    "ai-business"),   # github
    ("Tech Monitor",                                   "https://techmonitor.ai/feed",                                                             "ai-business"),   # github
    ("Techmeme",                                       "https://www.techmeme.com/feed.xml",                                                       "ai-business"),   # github
    ("Top Marketing AI",                               "https://topmarketingai.com/feed/",                                                        "ai-business"),   # feedspot
    ("ZDNET – AI",                                     "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",                             "ai-business"),   # github
    ("ZDNET – Big Data",                               "https://www.zdnet.com/topic/big-data/rss.xml",                                            "ai-business"),   # github

    # ── AI Dev: tools, libraries, SDKs, tutorials, infrastructure ────────────
    ("Hugging Face Blog",                              "https://huggingface.co/blog/feed.xml",                                                    "ai-dev"),      
    ("Towards Data Science",                           "https://towardsdatascience.com/feed",                                                     "ai-dev"),      
    ("NVIDIA Developer",                               "https://developer.nvidia.com/blog/feed",                                                  "ai-dev"),      
    ("AWS Machine Learning",                           "https://aws.amazon.com/blogs/machine-learning/feed/",                                     "ai-dev"),      
    ("AWS DevOps",                                     "https://aws.amazon.com/blogs/devops/feed/",                                               "ai-dev"),      
    ("Meta Engineering",                               "https://engineering.fb.com/feed",                                                         "ai-dev"),      
    ("Nanonets Blog",                                  "https://nanonets.com/blog/rss",                                                           "ai-dev"),      
    ("Kubernetes Blog",                                "https://kubernetes.io/feed.xml",                                                          "ai-dev"),      
    ("HashiCorp Blog",                                 "https://www.hashicorp.com/blog/feed.xml",                                                 "ai-dev"),      
    ("Databricks Docs",                                "https://docs.databricks.com/aws/en/feed.xml",                                             "ai-dev"),      
    ("arXiv cs.LG (ML)",                               "https://arxiv.org/rss/cs.LG",                                                             "ai-dev"),      
    ("arXiv stat.ML",                                  "https://arxiv.org/rss/stat.ML",                                                           "ai-dev"),      
    ("Product Hunt",                                   "https://www.producthunt.com/feed",                                                        "ai-dev"),      
    ("ByteByteGo",                                     "https://blog.bytebytego.com/feed",                                                        "ai-dev"),      
    ("Hacker News Front Page",                         "https://hnrss.org/frontpage",                                                             "ai-dev"),      
    ("Analytics Vidhya Blog",                          "https://www.analyticsvidhya.com/feed/",                                                   "ai-dev"),        # feedspot
    ("AWS Blog - Machine Learning/AI",                 "https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/feed/",    "ai-dev"),        # feedspot
    ("Blog Content – TOGETHER",                        "https://www.together.xyz/blog?format=rss",                                                "ai-dev"),        # github
    ("Blog – neptune.ai",                              "https://neptune.ai/blog/feed",                                                            "ai-dev"),        # github
    ("Blog – PyImageSearch",                           "https://pyimagesearch.com/blog/feed",                                                     "ai-dev"),        # github
    ("Chip Huyen",                                     "https://huyenchip.com/feed",                                                              "ai-dev"),        # github
    ("Context by Cohere",                              "https://txt.cohere.ai/rss/",                                                              "ai-dev"),        # github
    ("cs.CV updates on arXiv.org",                     "https://arxiv.org/rss/cs.CV",                                                             "ai-dev"),        # github
    ("DagsHub Blog",                                   "https://dagshub.com/blog/rss/",                                                           "ai-dev"),        # github
    ("Data Machina",                                   "https://datamachina.substack.com/feed",                                                   "ai-dev"),        # feedspot+github
    ("David Stutz Blog",                               "https://davidstutz.de/category/blog/feed",                                                "ai-dev"),        # github
    ("DebuggerCafe",                                   "https://debuggercafe.com/feed/",                                                          "ai-dev"),        # github
    ("Deephaven Blog",                                 "https://deephaven.io/blog/rss.xml",                                                       "ai-dev"),        # github
    ("DEV Community",                                  "https://dev.to/feed",                                                                     "ai-dev"),        # github
    ("EleutherAI Blog",                                "https://blog.eleuther.ai/index.xml",                                                      "ai-dev"),        # github
    ("Eugene Yan",                                     "https://eugeneyan.com/rss/",                                                              "ai-dev"),        # github
    ("Explosion",                                      "https://explosion.ai/feed",                                                               "ai-dev"),        # github
    ("Gradient Flow",                                  "https://gradientflow.com/feed/",                                                          "ai-dev"),        # github
    ("InfoQ – AI, ML & Data Engineering",              "https://feed.infoq.com/ai-ml-data-eng/",                                                  "ai-dev"),        # github
    ("InfoWorld Machine Learning",                     "https://www.infoworld.com/category/machine-learning/index.rss",                           "ai-dev"),        # github
    ("Interconnects",                                  "https://www.interconnects.ai/feed",                                                       "ai-dev"),        # github
    ("JMLR",                                           "https://www.jmlr.org/jmlr.xml",                                                           "ai-dev"),        # github
    ("KDnuggets",                                      "https://www.kdnuggets.com/feed",                                                          "ai-dev"),        # feedspot+github
    ("LangChain",                                      "https://blog.langchain.dev/rss/",                                                         "ai-dev"),        # github
    ("Latent Space",                                   "https://www.latent.space/feed",                                                           "ai-dev"),        # github
    ("Lightning AI",                                   "https://lightning.ai/pages/feed/",                                                        "ai-dev"),        # github
    ("Machine Learning Mastery Blog",                  "https://machinelearningmastery.com/blog/feed/",                                           "ai-dev"),        # feedspot+github
    ("Max Woolf's Blog",                               "https://minimaxir.com/post/index.xml",                                                    "ai-dev"),        # github
    ("MetaDevo AI Blog",                               "https://metadevo.com/feed/",                                                              "ai-dev"),        # feedspot
    ("Mila",                                           "https://mila.quebec/en/feed/",                                                            "ai-dev"),        # github
    ("Nicholas Carlini",                               "https://nicholas.carlini.com/writing/feed.xml",                                           "ai-dev"),        # github
    ("Paperspace Blog",                                "https://blog.paperspace.com/rss/",                                                        "ai-dev"),        # github
    ("R-bloggers",                                     "https://feeds.feedburner.com/RBloggers",                                                  "ai-dev"),        # github
    ("Replicate Blog",                                 "https://replicate.com/blog/rss",                                                          "ai-dev"),        # github
    ("SemiAnalysis",                                   "https://www.semianalysis.com/feed",                                                       "ai-dev"),        # github
    ("Simon Willison's Weblog",                        "https://simonwillison.net/atom/everything/",                                              "ai-dev"),        # github
    ("Stack Overflow Blog",                            "https://stackoverflow.blog/feed/",                                                        "ai-dev"),        # github
    ("Stanford CRFM",                                  "https://crfm.stanford.edu/feed",                                                          "ai-dev"),        # github
    ("The New Stack",                                  "https://thenewstack.io/feed",                                                             "ai-dev"),        # github
    ("The TensorFlow Blog",                            "https://blog.tensorflow.org/feeds/posts/default?alt=rss",                                 "ai-dev"),        # github
    ("Theodo Data & AI Blog",                          "https://data-ai.theodo.com/en/technical-blog/rss.xml",                                    "ai-dev"),        # feedspot
    ("Towards AI – Medium",                            "https://pub.towardsai.net/feed",                                                          "ai-dev"),        # github
    ("Weights & Biases: Fully Connected",              "https://wandb.ai/fully-connected/rss.xml",                                                "ai-dev"),        # github
    ("Wolfram Blog",                                   "https://blog.wolfram.com/feed/",                                                          "ai-dev"),        # github

    # ── Security: AI-driven threats, breaches, vulnerability research ─────────
    ("The Hacker News",                                "https://feeds.feedburner.com/TheHackersNews",                                             "security"),    
    ("Krebs on Security",                              "https://krebsonsecurity.com/feed/",                                                       "security"),    
    ("Dark Reading",                                   "https://www.darkreading.com/rss.xml",                                                     "security"),    
    ("Palo Alto Unit 42",                              "https://unit42.paloaltonetworks.com/feed/",                                               "security"),    
    ("Threatpost",                                     "https://threatpost.com/feed/",                                                            "security"),    
    ("Infosecurity Magazine",                          "https://www.infosecurity-magazine.com/rss/news/",                                         "security"),    
    ("Microsoft Security",                             "https://api.msrc.microsoft.com/update-guide/rss",                                         "security"),    
    ("The Verge Security",                             "https://www.theverge.com/rss/cyber-security/index.xml",                                   "security"),    
    ("Dark Reading",                                   "https://www.darkreading.com/rss_simple.asp",                                              "security"),      # github
    ("Hacker Noon – AI",                               "https://hackernoon.com/tagged/ai/feed",                                                   "security"),      # github

]
