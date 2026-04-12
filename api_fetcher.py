"""
API-based news fetchers: NewsAPI.org, GNews, Currents.
These return structured JSON with images + descriptions — no scraping needed.

Rate limit budgets (5-request buffer, 48 runs/day = every 30 min):
  NewsAPI  : (100  - 5) // 48 =  1 request/run  →  48 requests/day
  GNews    : (100  - 5) // 48 =  1 request/run  →  48 requests/day
  Currents : (1000 - 5) // 48 = 20 requests/run → 960 requests/day
"""

import requests
from config import NEWSAPI_KEY, GNEWS_KEY, CURRENTS_KEY, CATEGORIES, REQUEST_TIMEOUT, USER_AGENT
from fetcher import score_article

RUNS_PER_DAY = 48   # cron every 30 min

_NEWSAPI_MAX_PER_RUN  = (100  - 5) // RUNS_PER_DAY   # 1
_GNEWS_MAX_PER_RUN    = (100  - 5) // RUNS_PER_DAY   # 1
_CURRENTS_MAX_PER_RUN = (1000 - 5) // RUNS_PER_DAY   # 20

_HEADERS = {"User-Agent": USER_AGENT}


def _assign_category(article: dict) -> str:
    """
    Run keyword scoring against every category and return the best match.
    Falls back to 'API NEWS' if no category scores above 0.
    """
    best_cat   = "API NEWS"
    best_score = 0
    for cat in CATEGORIES:
        if cat["name"] == "GOOGLE ALERTS":
            continue
        s = score_article(article, cat["keywords"])
        if s > best_score:
            best_score = s
            best_cat   = cat["name"]
    return best_cat


def fetch_newsapi() -> list[dict]:
    """NewsAPI.org — top India headlines (100 req/day free)."""
    if not NEWSAPI_KEY or _NEWSAPI_MAX_PER_RUN < 1:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "in", "pageSize": 100, "apiKey": NEWSAPI_KEY},
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        articles = []
        for a in resp.json().get("articles", []):
            url = (a.get("url") or "").strip()
            if not url or url == "https://removed.com":
                continue
            articles.append({
                "title":       (a.get("title") or "").strip(),
                "url":         url,
                "description": (a.get("description") or "").strip()[:4000],
                "source":      a.get("source", {}).get("name") or "NewsAPI",
                "image":       a.get("urlToImage") or None,
                "published":   a.get("publishedAt", ""),
                "score":       0,
                "category":    "API NEWS",
            })
        print(f"  [newsapi] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [newsapi] error: {exc}")
        return []


def fetch_gnews() -> list[dict]:
    """GNews API — top India headlines (100 req/day free, max 10 per request on free tier)."""
    if not GNEWS_KEY or _GNEWS_MAX_PER_RUN < 1:
        return []
    try:
        resp = requests.get(
            "https://gnews.io/api/v4/top-headlines",
            params={"country": "in", "lang": "en", "max": 10, "token": GNEWS_KEY},
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        articles = []
        for a in resp.json().get("articles", []):
            url = (a.get("url") or "").strip()
            if not url:
                continue
            articles.append({
                "title":       (a.get("title") or "").strip(),
                "url":         url,
                "description": (a.get("description") or "").strip()[:4000],
                "source":      a.get("source", {}).get("name") or "GNews",
                "image":       a.get("image") or None,
                "published":   a.get("publishedAt", ""),
                "score":       0,
                "category":    "API NEWS",
            })
        print(f"  [gnews] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [gnews] error: {exc}")
        return []


def fetch_currents() -> list[dict]:
    """Currents API — latest India news (1000 req/day free)."""
    if not CURRENTS_KEY or _CURRENTS_MAX_PER_RUN < 1:
        return []
    try:
        resp = requests.get(
            "https://api.currentsapi.services/v1/latest-news",
            params={"language": "en", "country": "IN", "apiKey": CURRENTS_KEY},
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        articles = []
        for a in resp.json().get("news", []):
            url = (a.get("url") or "").strip()
            if not url:
                continue
            image = a.get("image")
            if not image or image == "None":
                image = None
            articles.append({
                "title":       (a.get("title") or "").strip(),
                "url":         url,
                "description": (a.get("description") or "").strip()[:4000],
                "source":      a.get("author") or "Currents",
                "image":       image,
                "published":   a.get("published", ""),
                "score":       0,
                "category":    "API NEWS",
            })
        print(f"  [currents] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [currents] error: {exc}")
        return []


def fetch_all_api_news() -> list[dict]:
    """
    Fetch from all three APIs, deduplicate by URL, then assign each article
    to the best-matching category via keyword scoring.
    """
    seen_urls: set[str] = set()
    combined: list[dict] = []

    for article in fetch_newsapi() + fetch_gnews() + fetch_currents():
        if article["url"] in seen_urls or not article["title"]:
            continue
        seen_urls.add(article["url"])
        article["category"] = _assign_category(article)
        article["score"]    = score_article(article, next(
            (c["keywords"] for c in CATEGORIES if c["name"] == article["category"]),
            []
        ))
        combined.append(article)

    return combined
