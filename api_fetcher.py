"""
API-based news fetchers: NewsAPI.org, GNews, Currents.
These return structured JSON with images + descriptions — no scraping needed.
"""

import requests
from config import NEWSAPI_KEY, GNEWS_KEY, CURRENTS_KEY, REQUEST_TIMEOUT, USER_AGENT

_HEADERS = {"User-Agent": USER_AGENT}


def fetch_newsapi() -> list[dict]:
    """NewsAPI.org — top India headlines (100 req/day free)."""
    if not NEWSAPI_KEY:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "in", "pageSize": 20, "apiKey": NEWSAPI_KEY},
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
                "description": (a.get("description") or "").strip()[:600],
                "source":      a.get("source", {}).get("name") or "NewsAPI",
                "image":       a.get("urlToImage") or None,
                "published":   a.get("publishedAt", ""),
                "score":       5,
                "category":    "API NEWS",
            })
        print(f"  [newsapi] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [newsapi] error: {exc}")
        return []


def fetch_gnews() -> list[dict]:
    """GNews API — top India headlines (100 req/day free)."""
    if not GNEWS_KEY:
        return []
    try:
        resp = requests.get(
            "https://gnews.io/api/v4/top-headlines",
            params={"country": "in", "lang": "en", "max": 20, "token": GNEWS_KEY},
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
                "description": (a.get("description") or "").strip()[:600],
                "source":      a.get("source", {}).get("name") or "GNews",
                "image":       a.get("image") or None,
                "published":   a.get("publishedAt", ""),
                "score":       5,
                "category":    "API NEWS",
            })
        print(f"  [gnews] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [gnews] error: {exc}")
        return []


def fetch_currents() -> list[dict]:
    """Currents API — latest India news (1000 req/day free)."""
    if not CURRENTS_KEY:
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
                "description": (a.get("description") or "").strip()[:600],
                "source":      a.get("author") or "Currents",
                "image":       image,
                "published":   a.get("published", ""),
                "score":       5,
                "category":    "API NEWS",
            })
        print(f"  [currents] fetched={len(articles)}")
        return articles
    except Exception as exc:
        print(f"  [currents] error: {exc}")
        return []


def fetch_all_api_news() -> list[dict]:
    """Fetch from all three APIs and deduplicate by URL."""
    seen_urls: set[str] = set()
    combined: list[dict] = []

    for article in fetch_newsapi() + fetch_gnews() + fetch_currents():
        if article["url"] in seen_urls or not article["title"]:
            continue
        seen_urls.add(article["url"])
        combined.append(article)

    return combined
