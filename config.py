import os

# ── Discord ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# ── Gemini ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Run settings ───────────────────────────────────────────────────────────────
MAX_ARTICLES_PER_CATEGORY = 3   # max sent to Discord per category per run
MIN_KEYWORD_SCORE         = 1   # articles scoring below this are dropped
REQUEST_TIMEOUT           = 12  # seconds for HTTP requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── Categories (ordered by priority — ALL India-focused) ──────────────────────
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
            "https://news.google.com/rss/search?q=india+top+news&hl=en-IN&gl=IN&ceid=IN:en",
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
            "https://feeds.feedburner.com/ndtvnews-india-news",
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
            "arunachal pradesh china", "india missile", "india nuclear",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=india+foreign+policy+border+conflict&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+pakistan+china+war+tension&hl=en-IN&gl=IN&ceid=IN:en",
            "https://www.thehindu.com/news/international/feeder/default.rss",
            "https://feeds.feedburner.com/ndtvnews-world-news",
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
            "india political party", "india political crisis",
            "india no confidence", "india referendum",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=india+politics+election+parliament&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=BJP+congress+AAP+india+political&hl=en-IN&gl=IN&ceid=IN:en",
            "https://feeds.feedburner.com/ndtvnews-india-news",
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
            "bollywood controversy", "india celebrity scandal",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=india+scandal+corruption+arrested+controversy&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+outrage+protest+scam+fraud&hl=en-IN&gl=IN&ceid=IN:en",
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
            "https://news.google.com/rss/search?q=india+economy+sensex+rbi+gdp&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+market+inflation+startup+budget&hl=en-IN&gl=IN&ceid=IN:en",
            "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
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
            "india executive order", "india cabinet decision",
            "india climate policy", "india environment",
            "india healthcare", "india education policy",
            "india infrastructure", "india tax reform",
            "india welfare scheme", "india yojana",
            "india digital", "india data protection",
            "india censorship", "india internet ban",
            "india upi", "india aadhaar policy",
        ],
        "feeds": [
            "https://news.google.com/rss/search?q=india+government+policy+ministry+law&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+supreme+court+cabinet+regulation&hl=en-IN&gl=IN&ceid=IN:en",
        ],
    },
]
