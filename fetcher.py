"""
RSS fetching, keyword scoring, image + description extraction.
"""

import re
import time
import base64
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from config import USER_AGENT, REQUEST_TIMEOUT

INDIA_TITLE_MUST = [
    # Country / national identifiers
    "india", "indian", "bharat", "hindustan",
    # Politicians
    "modi", "rahul gandhi", "amit shah", "yogi", "kejriwal",
    # Major cities
    "delhi", "mumbai", "bangalore", "bengaluru", "chennai",
    "hyderabad", "kolkata", "pune", "ahmedabad", "jaipur",
    "lucknow", "patna", "bhopal", "chandigarh", "surat",
    # States
    "uttar pradesh", "rajasthan", "gujarat", "maharashtra",
    "haryana", "kerala", "karnataka", "punjab", "bihar",
    "madhya pradesh", "assam", "bengal", "odisha", "jharkhand",
    # Institutions / markets
    "bjp", "congress", "lok sabha", "rajya sabha", "kashmir",
    "rbi", "sebi", "isro", "sensex", "nifty", "rupee",
    "pakistan", "india-china", "india-pak",
    # Religious / communal (for HINDU-MUSLIM category)
    "hindu", "muslim", "mosque", "temple", "masjid", "mandir",
    "communal", "waqf", "riot", "lynching", "conversion",
    "church", "sikh", "gurdwara",
]

_HEADERS = {
    "User-Agent":      USER_AGENT,
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


# ── Google News URL decoder ────────────────────────────────────────────────────

def _resolve_google_redirect(url: str) -> str:
    """
    Google Alerts links are redirect URLs like:
    https://www.google.com/url?rct=j&sa=t&url=https%3A%2F%2F...
    Extract the real article URL from the `url=` query parameter.
    """
    if "google.com/url" not in url:
        return url
    try:
        params = parse_qs(urlparse(url).query)
        real = params.get("url", [None])[0]
        if real and real.startswith("http"):
            return real
    except Exception:
        pass
    return url


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

def _extract_article_body(soup: BeautifulSoup) -> str | None:
    """
    Extract the main article body text from a parsed page.
    Tries common article containers first, falls back to collecting
    substantial <p> tags from anywhere on the page.
    """
    container = (
        soup.find("article") or
        soup.find(attrs={"class": re.compile(r"article[-_]?(body|text|content|detail)", re.I)}) or
        soup.find(attrs={"class": re.compile(r"story[-_]?(body|text|content|detail)", re.I)}) or
        soup.find(attrs={"class": re.compile(r"(news|post)[-_]?(body|text|content)", re.I)}) or
        soup.find("main")
    )

    if container:
        paras = [p.get_text(" ", strip=True) for p in container.find_all("p")
                 if len(p.get_text(strip=True)) > 40]
    else:
        # fallback: collect all substantial paragraphs from the whole page
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")
                 if len(p.get_text(strip=True)) > 60]

    if not paras:
        return None

    body = " ".join(paras[:6])   # first 6 paragraphs max
    return body[:1500] if len(body) > 100 else None


def scrape_article_meta(url: str) -> dict:
    """
    Decode Google News redirect URL first, then scrape the real article page
    for og:image, og:description, and article body text in a single HTTP call.
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

        # Try article body first — much richer than og:description
        body = _extract_article_body(soup)
        if body:
            result["description"] = body
        else:
            # Fall back to og:description / meta description
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

            # Resolve Google Alerts redirect URLs (google.com/url?url=...) to real article URLs
            is_google_alert = "google.com/url" in url
            url = _resolve_google_redirect(url)

            raw_summary = entry.get("summary", "")

            # ── image: try every RSS field in priority order ──────────────────
            image = None

            # 1. media:content  (Economic Times, Indian Express, many sites)
            for mc in entry.get("media_content", []):
                url_candidate = mc.get("url", "")
                if url_candidate.startswith("http") and "googleusercontent.com" not in url_candidate:
                    image = url_candidate
                    break

            # 2. media:thumbnail  (NDTV via FeedBurner, News18)
            #    Skip googleusercontent.com — those are Google's auto-generated
            #    title cards that visually repeat the headline, not real photos.
            if not image:
                for mt in entry.get("media_thumbnail", []):
                    url_candidate = mt.get("url", "")
                    if url_candidate.startswith("http") and "googleusercontent.com" not in url_candidate:
                        image = url_candidate
                        break

            # 3. enclosure  (Times of India)
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

            # ── description: prefer content:encoded (full article excerpt) ───
            # Many direct RSS feeds put 2-3 paragraphs in <content:encoded>
            # which is far richer than the short <description> snippet.
            rss_desc = ""
            for ct in entry.get("content", []):
                full_text = BeautifulSoup(
                    ct.get("value", ""), "html.parser"
                ).get_text(" ", strip=True)
                if len(full_text) > len(rss_desc):
                    rss_desc = full_text[:600]

            if not rss_desc:
                rss_desc = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)

            # Google Alerts titles often contain <b>keyword</b> HTML tags — strip them.
            # Also discard the RSS description for Google Alerts: it's the alert
            # snippet + query string, not real article content. _enrich() will
            # scrape the real article page for a proper description and image.
            raw_title = entry.get("title", "").strip()
            title = BeautifulSoup(raw_title, "html.parser").get_text(" ", strip=True)

            # For Google Alerts, extract the publisher name from the description
            # (it appears as "Article snippet - Publisher Name" in the HTML)
            # before we clear it.
            feed_source = feed.feed.get("title", "Unknown Source")
            if is_google_alert:
                src_match = re.search(r'-\s+([^<\n]+?)\s*(?:<br|$)', raw_summary)
                if src_match:
                    feed_source = src_match.group(1).strip()
                rss_desc = ""

            articles.append({
                "title":       title,
                "url":         url,
                "description": rss_desc,
                "source":      feed_source,
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
