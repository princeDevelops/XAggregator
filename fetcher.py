"""
RSS fetching, keyword scoring, image + description extraction.
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


# ── Article meta scraper ───────────────────────────────────────────────────────

def scrape_article_meta(url: str) -> dict:
    """
    Follow any redirects (handles Google News redirect URLs),
    then scrape og:image and og:description from the real article page.
    Returns {"image": str|None, "description": str|None}.
    """
    result = {"image": None, "description": None}
    try:
        resp     = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT,
                                allow_redirects=True)
        soup     = BeautifulSoup(resp.text, "html.parser")

        # image — try og:image then twitter:image
        for attr, name in [
            ("property", "og:image"),
            ("name",     "twitter:image"),
            ("property", "og:image:secure_url"),
        ]:
            tag = soup.find("meta", attrs={attr: name})
            val = tag.get("content", "") if tag else ""
            if val.startswith("http"):
                result["image"] = val
                break

        # description — try og:description then meta description
        for attr, name in [
            ("property", "og:description"),
            ("name",     "description"),
            ("name",     "twitter:description"),
        ]:
            tag = soup.find("meta", attrs={attr: name})
            val = (tag.get("content", "") if tag else "").strip()
            if len(val) > 40:          # ignore one-word or empty values
                result["description"] = val[:600]
                break

    except Exception as exc:
        print(f"  [fetcher] meta scrape failed ({url[:60]}): {exc}")

    return result


# ── RSS ────────────────────────────────────────────────────────────────────────

def fetch_feed(feed_url: str) -> list[dict]:
    """Parse one RSS feed, return list of raw article dicts."""
    try:
        feed     = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:20]:
            url = entry.get("link", "").strip()
            if not url:
                continue

            raw_summary = entry.get("summary", "")

            # image from RSS media tags (works for NDTV, ET, etc.)
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

            # description from RSS
            rss_desc = BeautifulSoup(
                raw_summary, "html.parser"
            ).get_text(" ", strip=True)

            articles.append({
                "title":       entry.get("title", "").strip(),
                "url":         url,
                "description": rss_desc,
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


# ── Main fetch for one category ────────────────────────────────────────────────

def fetch_category_articles(category: dict) -> list[dict]:
    seen_urls:    set[str]   = set()
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
