"""
Discord webhook integration.
Summary = RSS or scraped og:description.
No Gemini dependency.
"""

import time
import requests
from datetime import datetime, timezone

from config import DISCORD_WEBHOOK_URL, GOOGLE_ALERTS_WEBHOOK_URL

COLORS = {
    "INDIA":               0xFF9933,
    "GEOPOLITICS & WARS":  0xCC0000,
    "POLITICS":            0x1D6FA8,
    "SCANDALS & OUTRAGES": 0xFFAA00,
    "ECONOMY":             0x27AE60,
    "GOVT & POLICY":       0x8E44AD,
    "GOOGLE ALERTS":       0x4285F4,
}

EMOJIS = {
    "INDIA":               "🇮🇳",
    "GEOPOLITICS & WARS":  "🌍",
    "POLITICS":            "🏛️",
    "SCANDALS & OUTRAGES": "🔥",
    "ECONOMY":             "📈",
    "GOVT & POLICY":       "⚖️",
    "GOOGLE ALERTS":       "🔔",
}

# maps config webhook key → actual URL
_WEBHOOK_MAP = {
    "GOOGLE_ALERTS_WEBHOOK_URL": GOOGLE_ALERTS_WEBHOOK_URL,
}


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
