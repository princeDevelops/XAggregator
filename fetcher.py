"""
RSS fetching, keyword scoring, and image extraction.
"""

import time
import feedparser
import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, REQUEST_TIMEOUT

# India-specific keywords that MUST appear in the title for an article to pass.
# This hard-stops foreign news from leaking through.
INDIA_TITLE_MUST = [
    "india", "indian", "bharat", "modi", "delhi", "mumbai",
    "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata",
    "bjp", "congress", "lok sabha", "rajya sabha", "kashmir",
    "rbi", "sebi", "isro", "sensex", "nifty", "rupee",
    "pakistan", "india-china", "india-pak",
]


# ── RSS ────────────────────────────────────────────────────────────────────────

def _image_from_summary(summary_html: str) -> str | None:
    """
    Google News RSS embeds article thumbnails as <img> tags inside
    the description HTML (hosted on lh3.googleusercontent.com).
    Extract that before we discard the HTML.
    """
    if not summary_html:
        return None
    soup = BeautifulSoup(summary_html, "html.parser")
    img  = soup.find("img")
    if img:
        src = img.get("src", "")
        if src.startswith("http"):
            return src
    return None


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

            # 1. try RSS media tags first
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

            # 2. fall back to <img> inside the description HTML
            #    (Google News always has this — lh3.googleusercontent.com)
            if not image:
                image = _image_from_summary(raw_summary)

            articles.append({
                "title":       entry.get("title", "").strip(),
                "url":         url,
                "description": BeautifulSoup(
                    raw_summary, "html.parser"
                ).get_text(" ", strip=True)[:500],
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
    """
    Title match = 3 pts, description match = 1 pt.
    Minimum useful score is 3 (= at least one title hit).
    """
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
    """
    Hard gate: at least one core India keyword must appear in the title.
    Blocks foreign articles that only mention India in passing.
    """
    title = article["title"].lower()
    return any(kw in title for kw in INDIA_TITLE_MUST)


# ── og:image scrape (for non-Google-News feeds) ───────────────────────────────

def scrape_og_image(url: str) -> str | None:
    """Try to extract og:image from an article page. Skip Google News URLs."""
    if "news.google.com" in url:
        return None   # Google News redirect pages don't have og:image

    try:
        headers = {
            "User-Agent":      USER_AGENT,
            "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT,
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
    """
    Fetch all feeds for a category, score, deduplicate, and return
    sorted by score (highest first).
    """
    seen_urls: set[str] = set()
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
