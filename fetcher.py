"""
RSS fetching, keyword scoring, and image extraction.
"""

import time
import feedparser
import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, REQUEST_TIMEOUT

INDIA_TITLE_MUST = [
    "india", "indian", "bharat", "modi", "delhi", "mumbai",
    "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata",
    "bjp", "congress", "lok sabha", "rajya sabha", "kashmir",
    "rbi", "sebi", "isro", "sensex", "nifty", "rupee",
    "pakistan", "india-china", "india-pak",
]

_HEADERS = {
    "User-Agent":      USER_AGENT,
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


# ── Google News URL resolver ───────────────────────────────────────────────────

def _resolve_url(url: str) -> str:
    """
    Google News RSS links are redirect URLs (news.google.com/rss/articles/...).
    Follow the redirect chain to get the real article URL so we can
    scrape og:image from it.
    """
    if "news.google.com" not in url:
        return url
    try:
        # HEAD is faster — just follow redirects, don't download body
        resp = requests.head(url, headers=_HEADERS, timeout=8,
                             allow_redirects=True)
        final = resp.url
        # If HEAD lands back on Google, fall back to GET
        if "google.com" in final:
            resp = requests.get(url, headers=_HEADERS, timeout=8,
                                allow_redirects=True)
            final = resp.url
        return final if "google.com" not in final else url
    except Exception:
        return url


# ── RSS ────────────────────────────────────────────────────────────────────────

def fetch_feed(feed_url: str) -> list[dict]:
    """Parse one RSS feed and return a list of raw article dicts."""
    try:
        feed     = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:20]:
            url = entry.get("link", "").strip()
            if not url:
                continue

            raw_summary = entry.get("summary", "")

            # try RSS media tags for image
            image = None
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url")
            elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get("type", "").startswith("image/"):
                        image = enc.get("href") or enc.get("url")
                        break

            articles.append({
                "title":       entry.get("title", "").strip(),
                "url":         url,
                "description": BeautifulSoup(
                    raw_summary, "html.parser"
                ).get_text(" ", strip=True)[:600],
                "source":      feed.feed.get("title", "Unknown Source"),
                "published":   entry.get("published", ""),
                "image":       image,
                "score":       0,
                "category":    "",
            })
        return articles
    except Exception as exc:
        print(f"  [fetcher] feed error ({feed_url}): {exc}")
        return []


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_article(article: dict, keywords: list[str]) -> int:
    title = article["title"].lower()
    desc  = article["description"].lower()
    score = 0
    for kw in keywords:
        k = kw.lower()
        if k in title:
            score += 3
        if k in desc:
            score += 1
    return score


def is_india_relevant(article: dict) -> bool:
    title = article["title"].lower()
    return any(kw in title for kw in INDIA_TITLE_MUST)


# ── og:image scraping ──────────────────────────────────────────────────────────

def scrape_og_image(url: str) -> str | None:
    """
    Resolve the real article URL (follows Google News redirects),
    then extract og:image from it.
    """
    real_url = _resolve_url(url)
    try:
        resp = requests.get(real_url, headers=_HEADERS, timeout=REQUEST_TIMEOUT,
                            allow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        for attr, name in [
            ("property", "og:image"),
            ("name",     "twitter:image"),
            ("property", "og:image:secure_url"),
        ]:
            tag = soup.find("meta", attrs={attr: name})
            img = tag.get("content", "") if tag else ""
            if img.startswith("http"):
                return img
        return None
    except Exception:
        return None


# ── Main fetch for one category ────────────────────────────────────────────────

def fetch_category_articles(category: dict) -> list[dict]:
    seen_urls:    set[str]  = set()
    all_articles: list[dict] = []

    for feed_url in category["feeds"]:
        for article in fetch_feed(feed_url):
            if article["url"] in seen_urls:
                continue
            seen_urls.add(article["url"])
            article["score"]    = score_article(article, category["keywords"])
            article["category"] = category["name"]
            all_articles.append(article)
        time.sleep(0.5)

    all_articles.sort(key=lambda a: a["score"], reverse=True)
    return all_articles
