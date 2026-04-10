"""
RSS fetching, keyword scoring, image + description extraction.
"""

import re
import time
import base64
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


# ── Google News URL decoder ────────────────────────────────────────────────────

def _decode_gnews_url(url: str) -> str:
    """
    Google News RSS links are base64-encoded redirect URLs.
    Decode them directly to get the real article URL without any HTTP request.
    Falls back to the original URL on failure.
    """
    if "news.google.com" not in url:
        return url
    try:
        match = re.search(r'/articles/([A-Za-z0-9_\-]+)', url)
        if not match:
            return url
        token   = match.group(1)
        padded  = token + "=" * ((4 - len(token) % 4) % 4)
        decoded = base64.urlsafe_b64decode(padded).decode("latin-1", errors="replace")
        # the real URL is embedded as a printable string inside the binary blob
        url_match = re.search(r'https?://[^\x00-\x1f\x7f\s]+', decoded)
        if url_match:
            real = url_match.group(0).rstrip(".")
            if "google" not in real:
                return real
    except Exception:
        pass
    return url


# ── Article meta scraper ───────────────────────────────────────────────────────

def scrape_article_meta(url: str) -> dict:
    """
    Decode Google News redirect URL first, then scrape the real article page
    for og:image and og:description in a single HTTP call.
    """
    result   = {"image": None, "description": None}
    real_url = _decode_gnews_url(url)

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
            val = (tag.get("content", "") if tag else "").strip()
            if val.startswith("http"):
                result["image"] = val
                break

        for attr, name in [
            ("property", "og:description"),
            ("name",     "description"),
            ("name",     "twitter:description"),
        ]:
            tag = soup.find("meta", attrs={attr: name})
            val = (tag.get("content", "") if tag else "").strip()
            if len(val) > 40:
                result["description"] = val[:600]
                break

    except Exception as exc:
        print(f"  [fetcher] meta scrape failed: {exc}")

    return result


# ── RSS ────────────────────────────────────────────────────────────────────────

def _extract_image_from_html(html: str) -> str | None:
    """Pull the first <img src> out of an HTML string."""
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    tag  = soup.find("img")
    if tag:
        src = tag.get("src", "")
        if src.startswith("http"):
            return src
    return None


def fetch_feed(feed_url: str) -> list[dict]:
    try:
        feed     = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:20]:
            url = entry.get("link", "").strip()
            if not url:
                continue

            raw_summary = entry.get("summary", "")

            # ── image: try every RSS field in priority order ──────────────────
            image = None

            # 1. media:content   (ET, many sites)
            mc = entry.get("media_content", [])
            if mc and isinstance(mc, list):
                image = mc[0].get("url")

            # 2. media:thumbnail  (Google News, NDTV via FeedBurner)
            if not image:
                mt = entry.get("media_thumbnail", [])
                if mt and isinstance(mt, list):
                    image = mt[0].get("url")

            # 3. enclosure        (Times of India)
            if not image:
                for enc in entry.get("enclosures", []):
                    if enc.get("type", "").startswith("image/"):
                        image = enc.get("href") or enc.get("url")
                        break

            # 4. <img> inside content:encoded
            if not image:
                for ct in entry.get("content", []):
                    image = _extract_image_from_html(ct.get("value", ""))
                    if image:
                        break

            # 5. <img> inside description HTML
            if not image:
                image = _extract_image_from_html(raw_summary)

            # ── description: plain text from RSS ─────────────────────────────
            rss_desc = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)

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


# ── Scoring + India filter ─────────────────────────────────────────────────────

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
