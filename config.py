import os

# ── Discord ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL         = os.environ.get("DISCORD_WEBHOOK_URL", "")
GOOGLE_ALERTS_WEBHOOK_URL   = os.environ.get("GOOGLE_ALERTS_WEBHOOK_URL", "")
API_NEWS_WEBHOOK_URL        = os.environ.get("API_NEWS_WEBHOOK_URL", "")
HINDU_MUSLIM_WEBHOOK_URL    = os.environ.get("HINDU_MUSLIM_WEBHOOK_URL", "")
VIDEO_WEBHOOK_URL           = os.environ.get("VIDEO_WEBHOOK_URL", "")

# ── YouTube channels ───────────────────────────────────────────────────────────
YOUTUBE_CHANNELS = {
    "NDTV India":  "UC9CYT9gSNLevX5ey2_6CK0Q",
    "NDTV":        "UCZFMm1mMw0F81Z37aaEzTUA",
    "Aaj Tak":     "UCt4t-jeY85JegMlZ-E5UWtA",
    "India Today": "UCYPvAwZP8pZhSMW8qs7cVCw",
    "Zee News":    "UCIvaYmXn910QMdemBG3v1pQ",
    "News18":      "UCPP3etACgdUWvizcES1dJ8Q",
    "ET Now":      "UCI_mwTKUhicNzFrhm33MzBQ",
    "WION":        "UC_gUM8rL-Lrg6O3adPW9K1g",
    "ABP News":    "UCRWFSbif-RFENbBrSiez1DA",
    "Times Now":   "UC6RJ7-PaXg6TIH2BzZfTV7w",
    "Republic TV": "UCwqusr8YDwM-3mEYTDeJHzw",
}

# ── News APIs ──────────────────────────────────────────────────────────────────
NEWSAPI_KEY   = os.environ.get("NEWSAPI_KEY", "")
GNEWS_KEY     = os.environ.get("GNEWS_KEY", "")
CURRENTS_KEY  = os.environ.get("CURRENTS_KEY", "")

# ── Gemini ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Keyword watchlist ──────────────────────────────────────────────────────────
# Articles whose title or description contains any of these (case-insensitive)
# will trigger an instant alert in the main Discord channel.
WATCHLIST = [
    "adani", "ambani", "rahul gandhi arrested", "modi arrested",
    "nuclear", "war declared", "ceasefire", "coup",
    "earthquake", "flood", "terror attack", "bomb blast",
    "stock market crash", "rupee crash", "rbi rate",
    "supreme court verdict", "election results",
]

# ── Run settings ───────────────────────────────────────────────────────────────
MAX_ARTICLES_PER_CATEGORY = 50
MIN_KEYWORD_SCORE         = 3
REQUEST_TIMEOUT           = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── Categories ─────────────────────────────────────────────────────────────────
CATEGORIES = [
    {
        "name":          "INDIA",
        "emoji":         "🇮🇳",
        "priority":      1,
        "gemini_budget": 400,
        "color":         0xFF9933,
        "keywords": [
            "india", "indian", "bharat", "hindustan",
            "modi", "narendra modi", "pm modi", "rahul gandhi",
            "amit shah", "yogi adityanath", "smriti irani", "rajnath singh",
            "delhi", "mumbai", "bangalore", "bengaluru", "chennai",
            "hyderabad", "kolkata", "pune", "ahmedabad", "jaipur",
            "bjp", "congress party", "aam aadmi party", "aap",
            "lok sabha", "rajya sabha", "india parliament",
            "rbi", "sebi", "isro", "drdo", "supreme court of india",
            "sensex", "nifty", "rupee", "indian army", "indian navy",
        ],
        "feeds": [
            "https://feeds.feedburner.com/ndtvnews-india-news",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "https://indianexpress.com/section/india/feed/",
            "https://www.news18.com/rss/india.xml",
            "https://feeds.reuters.com/reuters/INtopNews",
            "https://www.aninews.in/rss/all.xml",
            "https://swarajyamag.com/feed",
            "https://www.opindia.com/feed/",
        ],
    },
    {
        "name":          "GEOPOLITICS & WARS",
        "emoji":         "🌍",
        "priority":      2,
        "gemini_budget": 300,
        "color":         0xCC0000,
        "keywords": [
            "india pakistan", "india china", "india border",
            "line of control", "loc", "lac", "kashmir conflict",
            "india foreign policy", "india us relations", "india russia",
            "india israel", "india iran", "india sri lanka",
            "india nepal", "india bangladesh", "india maldives",
            "india myanmar", "india bhutan", "quad",
            "india military", "indian army deployed", "indian navy",
            "ceasefire india", "india sanctions", "india un",
            "india g20", "india sco", "india brics",
            "pakistan terror", "china aggression", "doklam",
            "arunachal pradesh", "india missile", "india nuclear",
        ],
        "feeds": [
            "https://www.thehindu.com/news/international/feeder/default.rss",
            "https://feeds.feedburner.com/ndtvnews-world-news",
            "https://indianexpress.com/section/world/feed/",
            "https://timesofindia.indiatimes.com/rssfeeds/-2128672765.cms",
            "https://feeds.reuters.com/reuters/INdomesticNews",
            "https://www.aninews.in/rss/all.xml",
            "https://swarajyamag.com/feed",
        ],
    },
    {
        "name":          "POLITICS",
        "emoji":         "🏛️",
        "priority":      3,
        "gemini_budget": 150,
        "color":         0x1D6FA8,
        "keywords": [
            "bjp", "congress", "aap", "aam aadmi party", "sp", "bsp", "tmc",
            "india election", "state election", "assembly election",
            "lok sabha", "rajya sabha", "india parliament session",
            "modi government", "opposition india", "india coalition",
            "india political", "india vote", "india campaign",
            "india president", "india pm", "india chief minister",
            "india minister", "india mla", "india mp",
            "india political crisis", "india no confidence",
        ],
        "feeds": [
            "https://feeds.feedburner.com/ndtvnews-politics-news",
            "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeed.cms",
            "https://www.news18.com/rss/politics.xml",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://www.aninews.in/rss/all.xml",
            "https://www.opindia.com/feed/",
            "https://swarajyamag.com/feed",
        ],
    },
    {
        "name":          "SCANDALS & OUTRAGES",
        "emoji":         "🔥",
        "priority":      4,
        "gemini_budget": 200,
        "color":         0xFFAA00,
        "keywords": [
            "india scandal", "india corruption", "india fraud", "india scam",
            "india arrested", "india politician arrested", "india minister arrested",
            "india controversy", "india resign", "india sacked",
            "india cover-up", "india leaked", "india exposed",
            "india outrage", "india backlash", "india protest",
            "india rape", "india murder", "india crime",
            "india cbi", "india ed", "india enforcement directorate",
            "india money laundering", "india bribery",
            "india whistleblower", "india probe", "india inquiry",
            "india riot", "india violence", "india attack",
            "bollywood controversy", "india celebrity",
        ],
        "feeds": [
            "https://feeds.feedburner.com/ndtvnews-crime-news",
            "https://www.news18.com/rss/india.xml",
            "https://indianexpress.com/section/india/feed/",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "https://www.aninews.in/rss/all.xml",
            "https://www.opindia.com/feed/",
        ],
    },
    {
        "name":          "ECONOMY",
        "emoji":         "📈",
        "priority":      5,
        "gemini_budget": 150,
        "color":         0x27AE60,
        "keywords": [
            "india economy", "indian economy", "india gdp",
            "sensex", "nifty", "bse", "nse", "india market",
            "rbi", "reserve bank of india", "india interest rate",
            "india inflation", "india recession", "india growth",
            "rupee", "india rupee", "india forex",
            "india budget", "india fiscal", "india tax",
            "india startup", "india unicorn", "india ipo",
            "india trade", "india export", "india import",
            "india tariff", "india fdi", "india investment",
            "india unemployment", "india jobs", "india layoffs",
            "india oil price", "india fuel", "adani", "ambani", "tata",
        ],
        "feeds": [
            "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
            "https://economictimes.indiatimes.com/news/economy/rssfeed.cms",
            "https://feeds.feedburner.com/ndtvnews-business-news",
            "https://www.thehindu.com/business/feeder/default.rss",
            "https://indianexpress.com/section/business/feed/",
            "https://feeds.reuters.com/reuters/INbusinessNews",
            "https://www.livemint.com/rss/news",
        ],
    },
    {
        "name":          "GOVT & POLICY",
        "emoji":         "⚖️",
        "priority":      6,
        "gemini_budget": 150,
        "color":         0x8E44AD,
        "keywords": [
            "india new law", "india legislation", "india bill passed",
            "india government policy", "india regulation",
            "india ministry", "india ministry announcement",
            "india supreme court", "india high court", "india court ruling",
            "india cabinet decision", "india executive order",
            "india climate policy", "india environment",
            "india healthcare", "india education policy",
            "india infrastructure", "india tax reform",
            "india welfare scheme", "india yojana",
            "india digital", "india data protection",
            "india upi", "india aadhaar",
        ],
        "feeds": [
            "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeed.cms",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://indianexpress.com/section/india/feed/",
            "https://feeds.feedburner.com/ndtvnews-india-news",
            "https://www.aninews.in/rss/all.xml",
            "https://www.livemint.com/rss/news",
        ],
    },
    {
        "name":          "HINDU-MUSLIM",
        "emoji":         "🛕",
        "priority":      8,
        "gemini_budget": 0,
        "color":         0xFF6B00,
        "webhook":       "HINDU_MUSLIM_WEBHOOK_URL",
        "keywords": [
            # Communal violence / riots
            "communal violence", "communal riot", "communal clash",
            "hindu muslim clash", "religious violence", "mob lynching",
            "lynching india", "cow vigilante", "bajrang dal", "vhp attack",
            # Conversion / Love Jihad
            "love jihad", "forced conversion", "conversion racket",
            "ghar wapsi", "religious conversion india", "hindu conversion",
            "anti-conversion law", "conversion controversy india",
            # Temple / Mosque disputes
            "temple demolition", "mosque demolition", "temple mosque dispute",
            "waqf board", "waqf controversy", "masjid controversy",
            "mandir controversy", "places of worship act",
            # Murder / Attack by religion
            "hindu killed", "muslim killed", "hindu murder", "muslim murder",
            "priest attacked", "maulana arrested", "imam arrested",
            "hindu monk killed",
            # Hate speech / Incitement
            "hate speech india", "religious slur india", "islamophobia india",
            "anti-hindu", "minority attack india", "majority attack india",
            # Political / Legal
            "ucc uniform civil code", "triple talaq", "population jihad",
            "land jihad", "halal controversy india", "hijab ban india",
            "azaan controversy", "loudspeaker mosque",
            # Organizations
            "popular front india", "pfi banned", "hindu mahasabha",
            # Corporate / Economic jihad
            "corporate jihad", "economic boycott hindu", "hindu boycott",
            "halal economy", "halal certification controversy",
            "halal products ban", "islamic banking india",
            "muslim business boycott", "hindu business attack",
            "economic jihad", "land grab india", "demographic jihad",
            "urban jihad",
        ],
        "feeds": [
            "https://www.opindia.com/feed/",
            "https://swarajyamag.com/feed",
            "https://feeds.feedburner.com/ndtvnews-india-news",
            "https://www.news18.com/rss/india.xml",
            "https://indianexpress.com/section/india/feed/",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "https://www.aninews.in/rss/all.xml",
        ],
    },
    {
        "name":          "GOOGLE ALERTS",
        "emoji":         "🔔",
        "priority":      7,
        "gemini_budget": 0,
        "color":         0x4285F4,
        "webhook":       "GOOGLE_ALERTS_WEBHOOK_URL",   # sends to separate channel
        "skip_filters":  True,   # Google Alert query already ensures relevance
        "keywords": [
            "india", "indian", "bharat",
        ],
        "feeds": [
            "https://www.google.com/alerts/feeds/14698970451173461670/10712801714031529639",
        ],
    },
]
