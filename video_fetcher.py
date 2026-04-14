"""
YouTube video fetcher.
Pulls latest videos from Indian news channels via YouTube RSS feeds.
No API key required — YouTube provides public RSS for every channel.

RSS format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
Returns the 15 most recent uploads per channel.
"""

import time
import feedparser
from bs4 import BeautifulSoup

from config import YOUTUBE_CHANNELS, CATEGORIES
from fetcher import score_article


def _best_thumbnail(entry) -> str | None:
    """Return the highest-quality thumbnail available for a YouTube entry."""
    # feedparser exposes media:thumbnail as a list sorted by size
    thumbnails = entry.get("media_thumbnail", [])
    if thumbnails:
        # prefer the largest one (last in list or highest width)
        best = max(thumbnails, key=lambda t: int(t.get("width", 0)), default=thumbnails[0])
        url = best.get("url", "")
        if url.startswith("http"):
            # upgrade to hqdefault if we got a low-res default thumb
            url = url.replace("/default.jpg", "/hqdefault.jpg")
            return url
    return None


def _clean_description(raw: str) -> str:
    """Strip HTML from YouTube RSS summary field."""
    if not raw:
        return ""
    return BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)[:4000]


def fetch_youtube_channel(channel_id: str, channel_name: str) -> list[dict]:
    """Fetch the 15 most recent videos from one YouTube channel."""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        feed = feedparser.parse(feed_url)
        videos = []
        for entry in feed.entries[:15]:
            url = entry.get("link", "").strip()
            if not url or "youtube.com/watch" not in url:
                continue

            title = entry.get("title", "").strip()
            if not title:
                continue

            desc = _clean_description(entry.get("summary", ""))

            videos.append({
                "title":       title,
                "url":         url,
                "description": desc,
                "source":      channel_name,
                "image":       _best_thumbnail(entry),
                "published":   entry.get("published", ""),
                "score":       0,
                "category":    "VIDEO",
                "is_video":    True,
            })
        return videos
    except Exception as exc:
        print(f"  [youtube] {channel_name} error: {exc}")
        return []


def fetch_all_videos() -> list[dict]:
    """
    Fetch from all configured YouTube channels, deduplicate by URL,
    then assign each video to the best-matching category via keyword scoring.
    Falls back to 'VIDEO' if nothing scores above 0.
    """
    seen_urls: set[str] = set()
    combined: list[dict] = []

    for channel_name, channel_id in YOUTUBE_CHANNELS.items():
        videos = fetch_youtube_channel(channel_id, channel_name)
        print(f"  [youtube] {channel_name}: fetched={len(videos)}")

        for video in videos:
            if video["url"] in seen_urls or not video["title"]:
                continue
            seen_urls.add(video["url"])

            # assign best category
            best_cat   = "VIDEO"
            best_score = 0
            for cat in CATEGORIES:
                if cat["name"] in ("GOOGLE ALERTS", "VIDEO"):
                    continue
                s = score_article(video, cat["keywords"])
                if s > best_score:
                    best_score = s
                    best_cat   = cat["name"]

            video["category"] = best_cat
            video["score"]    = best_score
            combined.append(video)

        time.sleep(0.3)

    return combined
