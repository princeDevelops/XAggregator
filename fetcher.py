"""
RSS fetching, keyword scoring, and og:image extraction.
"""

import time
import feedparser
import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, REQUEST_TIMEOUT


# ── RSS ────────────────────────────────────────────────────────────────────────

def fetch_feed(feed_url: str) -> list[dict]:
    """Parse one RSS feed and return a list of raw article dicts."""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        for entry in feed.entries[:20]:          # cap at 20 most-recent entries
            url = entry.get("link", "").strip()
            if not url:
                continue

            # pull image from RSS enclosure / media tags if present
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
                    entry.get("summary", ""), "html.parser"
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
    Return a relevance score.
    Title match = 3 pts, description match = 1 pt (case-insensitive).
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


# ── Image scraping ─────────────────────────────────────────────────────────────

def scrape_og_image(url: str) -> str | None:
    """Try to extract og:image or twitter:image from an article page."""
    try:
        headers  = {"User-Agent": USER_AGENT}
        resp     = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        soup     = BeautifulSoup(resp.text, "html.parser")

        for attr, name in [
            ("property", "og:image"),
            ("name",     "twitter:image"),
            ("property", "og:image:secure_url"),
        ]:
            tag = soup.find("meta", attrs={attr: name})
            if tag and tag.get("content", "").startswith("http"):
                return tag["content"]
        return None
    except Exception:
        return None


# ── Main fetch for one category ────────────────────────────────────────────────

def fetch_category_articles(category: dict) -> list[dict]:
    """
    Fetch all feeds for a category, score, deduplicate within the batch,
    and return sorted (highest score first).
    """
    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    for feed_url in category["feeds"]:
        articles = fetch_feed(feed_url)
        for article in articles:
            if article["url"] in seen_urls:
                continue
            seen_urls.add(article["url"])

            article["score"]    = score_article(article, category["keywords"])
            article["category"] = category["name"]
            all_articles.append(article)

        time.sleep(0.5)   # be polite between feed requests

    all_articles.sort(key=lambda a: a["score"], reverse=True)
    return all_articles
