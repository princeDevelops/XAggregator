"""
Discord webhook integration.
Summary = RSS or scraped og:description.
No Gemini dependency.
"""

import time
import requests
from datetime import datetime, timezone

from config import DISCORD_WEBHOOK_URL, GOOGLE_ALERTS_WEBHOOK_URL, API_NEWS_WEBHOOK_URL

COLORS = {
    "INDIA":               0xFF9933,
    "GEOPOLITICS & WARS":  0xCC0000,
    "POLITICS":            0x1D6FA8,
    "SCANDALS & OUTRAGES": 0xFFAA00,
    "ECONOMY":             0x27AE60,
    "GOVT & POLICY":       0x8E44AD,
    "GOOGLE ALERTS":       0x4285F4,
    "API NEWS":            0x00B4D8,
    "HINDU-MUSLIM":        0xFF6B00,
}

EMOJIS = {
    "INDIA":               "🇮🇳",
    "GEOPOLITICS & WARS":  "🌍",
    "POLITICS":            "🏛️",
    "SCANDALS & OUTRAGES": "🔥",
    "ECONOMY":             "📈",
    "GOVT & POLICY":       "⚖️",
    "GOOGLE ALERTS":       "🔔",
    "API NEWS":            "📡",
    "HINDU-MUSLIM":        "🛕",
}

# maps config webhook key → actual URL
_WEBHOOK_MAP = {
    "GOOGLE_ALERTS_WEBHOOK_URL": GOOGLE_ALERTS_WEBHOOK_URL,
    "API_NEWS_WEBHOOK_URL":      API_NEWS_WEBHOOK_URL,
}


def send_run_summary(counts: dict[str, int], trending_count: int) -> bool:
    """
    Post a run summary message to the main Discord channel.
    counts = { "INDIA": 15, "GEOPOLITICS & WARS": 12, ... }
    """
    total = sum(counts.values())
    now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # build per-category line
    lines = []
    for name, count in counts.items():
        if name == "GOOGLE ALERTS":
            continue   # excluded from main summary
        emoji = EMOJIS.get(name, "📰")
        lines.append(f"{emoji} {name.title()}: **{count}**")

    # chunk into rows of 3
    rows = []
    for i in range(0, len(lines), 3):
        rows.append("   ".join(lines[i:i+3]))

    trending_line = f"🔴 Trending stories flagged: **{trending_count}**\n" if trending_count else ""

    description = trending_line + "\n".join(rows)

    embed = {
        "title":       f"✅ Run complete — {total} articles sent",
        "description": description,
        "color":       0x2ECC71,
        "footer":      {"text": now_utc},
    }

    payload = {"embeds": [embed]}

    for attempt in range(2):
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code == 429:
                wait = resp.json().get("retry_after", 2)
                time.sleep(float(wait) + 0.5)
                continue
            resp.raise_for_status()
            return True
        except Exception as exc:
            print(f"  [discord] summary send error (attempt {attempt + 1}): {exc}")
            time.sleep(1)

    return False


def send_trending(trending_story: dict) -> bool:
    """
    Send a 🔴 TRENDING alert embed to the main Discord channel.
    Uses the representative article's image and description.
    """
    rep      = trending_story["representative"]
    sources  = trending_story["sources"]
    count    = trending_story["count"]
    category = rep["category"]
    emoji    = EMOJIS.get(category, "📰")
    now_utc  = datetime.now(timezone.utc).strftime("%H:%M UTC")

    source_list = " • ".join(sources[:6])   # cap display at 6 sources
    if len(sources) > 6:
        source_list += f" +{len(sources) - 6} more"

    description = (
        f"**{count} sources are covering this story right now.**\n"
        f"{source_list}\n\n"
        f"{rep.get('description', '').strip()}"
    ).strip()

    embed: dict = {
        "author":      {"name": f"🔴  TRENDING  •  {emoji} {category}"},
        "title":       rep["title"][:256],
        "url":         rep["url"],
        "description": description[:4096],
        "color":       0xFF0000,
        "footer":      {"text": f"📰 {rep['source']}   •   {now_utc}"},
    }

    if rep.get("image"):
        embed["image"] = {"url": rep["image"]}

    payload = {"embeds": [embed]}

    for attempt in range(2):
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code == 429:
                wait = resp.json().get("retry_after", 2)
                print(f"  [discord] rate-limited, waiting {wait}s")
                time.sleep(float(wait) + 0.5)
                continue
            resp.raise_for_status()
            return True
        except Exception as exc:
            print(f"  [discord] trending send error (attempt {attempt + 1}): {exc}")
            time.sleep(1)

    return False


def send_failure_alert() -> bool:
    """Post a red alert to the main channel when a run sends 0 articles."""
    now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
    embed = {
        "title":       "⚠️ XAggregator — Run sent 0 articles",
        "description": "No articles were sent this run. Check GitHub Actions logs for errors.",
        "color":       0xFF0000,
        "footer":      {"text": now_utc},
    }
    payload = {"embeds": [embed]}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"  [discord] failure alert error: {exc}")
        return False


def send_watchlist_alert(article: dict, keyword: str) -> bool:
    """Post a 🚨 alert when a sent article matches a watchlist keyword."""
    now_utc  = datetime.now(timezone.utc).strftime("%H:%M UTC")
    category = article.get("category", "")
    emoji    = EMOJIS.get(category, "📰")

    embed = {
        "author":      {"name": f"🚨  WATCHLIST HIT  •  {emoji} {category}"},
        "title":       article["title"][:256],
        "url":         article["url"],
        "description": f"**Matched keyword:** `{keyword}`\n\n{article.get('description', '').strip()[:300]}",
        "color":       0xFF4500,
        "footer":      {"text": f"📰 {article['source']}   •   {now_utc}"},
    }
    if article.get("image"):
        embed["image"] = {"url": article["image"]}

    payload = {"embeds": [embed]}
    for attempt in range(2):
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code == 429:
                wait = resp.json().get("retry_after", 2)
                time.sleep(float(wait) + 0.5)
                continue
            resp.raise_for_status()
            return True
        except Exception as exc:
            print(f"  [discord] watchlist alert error (attempt {attempt + 1}): {exc}")
            time.sleep(1)
    return False


def send_article(article: dict, webhook_key: str | None = None) -> bool:
    category = article["category"]
    emoji    = EMOJIS.get(category, "📰")
    color    = COLORS.get(category, 0x808080)
    now_utc  = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # use category-specific webhook if provided, else default
    webhook_url = _WEBHOOK_MAP.get(webhook_key, DISCORD_WEBHOOK_URL) if webhook_key else DISCORD_WEBHOOK_URL
    if not webhook_url:
        print(f"  [discord] no webhook URL for key '{webhook_key}' — skipping")
        return False

    description = article.get("description", "").strip() or "*No description available.*"

    embed: dict = {
        "author":      {"name": f"{emoji}  {category}"},
        "title":       article["title"][:256],
        "url":         article["url"],
        "description": description[:4096],
        "color":       color,
        "footer":      {"text": f"📰 {article['source']}   •   {now_utc}"},
    }

    if article.get("image"):
        embed["image"] = {"url": article["image"]}

    if article.get("caption"):
        embed["fields"] = [{"name": "📸 Instagram Caption", "value": article["caption"][:1024], "inline": False}]

    payload = {"embeds": [embed]}

    for attempt in range(2):
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code == 429:
                wait = resp.json().get("retry_after", 2)
                print(f"  [discord] rate-limited, waiting {wait}s")
                time.sleep(float(wait) + 0.5)
                continue
            resp.raise_for_status()
            return True
        except Exception as exc:
            print(f"  [discord] error (attempt {attempt + 1}): {exc}")
            time.sleep(1)

    return False
