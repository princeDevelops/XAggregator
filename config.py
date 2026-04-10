import os

# ── Discord ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# ── Gemini ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-1.5-flash"

# ── Run settings ───────────────────────────────────────────────────────────────
MAX_ARTICLES_PER_CATEGORY = 3   # max sent to Discord per category per run
MIN_KEYWORD_SCORE         = 1   # articles scoring below this are dropped
REQUEST_TIMEOUT           = 10  # seconds for HTTP requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── Categories (ordered by priority) ──────────────────────────────────────────
# gemini_budget = max Gemini calls per day for this category
# color         = Discord embed sidebar color (hex int)
CATEGORIES = [
    {
        "name":           "INDIA",
        "emoji":          "🇮🇳",
        "priority":       1,
        "gemini_budget":  400,
        "color":          0xFF9933,
        "keywords": [
            # identity
            "india", "indian", "bharat", "hindustan",
            # leadership
            "modi", "narendra modi", "pm modi", "rahul gandhi",
            "amit shah", "yogi adityanath", "smriti irani",
            # cities / states
            "delhi", "mumbai", "bangalore", "bengaluru", "chennai",
            "hyderabad", "kolkata", "pune", "ahmedabad", "jaipur",
            # institutions
            "bjp", "congress party", "aam aadmi party", "aap",
            "lok sabha", "rajya sabha", "india parliament",
            "rbi", "sebi", "isro", "drdo", "supreme court of india",
            # borders / conflicts
            "india-pakistan", "india-china", "line of control",
            "lac border", "kashmir", "arunachal", "doklam",
            # economy markers
            "sensex", "nifty", "rupee", "indian economy",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "https://feeds.feedburner.com/ndtvnews-top-stories",
        ],
    },
    {
        "name":           "GEOPOLITICS & WARS",
        "emoji":          "🌍",
        "priority":       2,
        "gemini_budget":  300,
        "color":          0xCC0000,
        "keywords": [
            "war", "conflict", "invasion", "airstrike", "missile strike",
            "ceasefire", "offensive", "troops", "military operation",
            "nato", "sanctions", "nuclear", "geopolitics",
            "russia", "ukraine", "putin", "zelensky",
            "china", "taiwan", "xi jinping", "south china sea",
            "israel", "palestine", "gaza", "hamas", "hezbollah",
            "iran", "north korea", "kim jong un",
            "diplomacy", "treaty", "alliance", "g7", "g20",
            "un security council", "united nations", "pentagon",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=geopolitics+war+conflict&hl=en-US&gl=US&ceid=US:en",
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.reuters.com/reuters/worldNews",
        ],
    },
    {
        "name":           "POLITICS",
        "emoji":          "🏛️",
        "priority":       3,
        "gemini_budget":  150,
        "color":          0x1D6FA8,
        "keywords": [
            "election", "elections", "voting", "ballot",
            "government", "parliament", "senate", "congress",
            "president", "prime minister", "cabinet minister",
            "democrat", "republican", "liberal", "conservative",
            "trump", "biden", "harris", "macron", "sunak", "scholz",
            "campaign", "referendum", "coup", "political crisis",
            "opposition", "ruling party", "coalition",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=politics+election+government&hl=en-US&gl=US&ceid=US:en",
            "https://feeds.bbci.co.uk/news/politics/rss.xml",
        ],
    },
    {
        "name":           "SCANDALS & OUTRAGES",
        "emoji":          "🔥",
        "priority":       4,
        "gemini_budget":  200,
        "color":          0xFFAA00,
        "keywords": [
            "scandal", "corruption", "fraud", "scam", "bribery",
            "arrested", "indicted", "charged", "convicted", "sentenced",
            "controversy", "resign", "resigned", "fired", "sacked",
            "cover-up", "coverup", "leaked", "leak", "exposed",
            "outrage", "backlash", "protests erupted",
            "abuse", "misconduct", "harassment", "assault",
            "embezzlement", "money laundering", "whistleblower",
            "investigation launched", "probe ordered",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=scandal+corruption+fraud+controversy&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=outrage+backlash+resigned+arrested&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "name":           "ECONOMY",
        "emoji":          "📈",
        "priority":       5,
        "gemini_budget":  150,
        "color":          0x27AE60,
        "keywords": [
            "economy", "economic crisis", "inflation", "recession",
            "gdp", "market crash", "stock market", "wall street",
            "federal reserve", "interest rate", "rate hike", "rate cut",
            "trade war", "tariff", "oil price", "energy crisis",
            "unemployment", "layoffs", "jobs report",
            "imf", "world bank", "fiscal policy", "monetary policy",
            "budget deficit", "debt ceiling", "financial crisis",
            "bitcoin", "cryptocurrency", "crypto crash",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=economy+inflation+recession+markets&hl=en-US&gl=US&ceid=US:en",
            "https://feeds.reuters.com/reuters/businessNews",
        ],
    },
    {
        "name":           "GOVT & POLICY",
        "emoji":          "⚖️",
        "priority":       6,
        "gemini_budget":  150,
        "color":          0x8E44AD,
        "keywords": [
            "new law", "legislation passed", "bill signed",
            "government policy", "regulation", "executive order",
            "ministry announcement", "federal agency",
            "climate policy", "environment regulation",
            "healthcare policy", "education policy",
            "infrastructure plan", "tax reform", "welfare",
            "supreme court ruling", "court verdict", "court order",
            "white house", "cabinet reshuffle", "governance",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=government+policy+legislation+law&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=supreme+court+ruling+executive+order&hl=en-US&gl=US&ceid=US:en",
        ],
    },
]
