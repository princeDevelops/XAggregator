"""
Discord webhook integration.
Summary = RSS or scraped og:description.
No Gemini dependency.
"""

import time
import requests
from datetime import datetime, timezone

from config import DISCORD_WEBHOOK_URL

COLORS = {
    "INDIA":               0xFF9933,
    "GEOPOLITICS & WARS":  0xCC0000,
    "POLITICS":            0x1D6FA8,
    "SCANDALS & OUTRAGES": 0xFFAA00,
    "ECONOMY":             0x27AE60,
    "GOVT & POLICY":       0x8E44AD,
}

EMOJIS = {
    "INDIA":               "🇮🇳",
    "GEOPOLITICS & WARS":  "🌍",
    "POLITICS":            "🏛️",
    "SCANDALS & OUTRAGES": "🔥",
    "ECONOMY":             "📈",
    "GOVT & POLICY":       "⚖️",
}


def send_article(article: dict) -> bool:
    category = article["category"]
    emoji    = EMOJIS.get(category, "📰")
    color    = COLORS.get(category, 0x808080)
    now_utc  = datetime.now(timezone.utc).strftime("%H:%M UTC")

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
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
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
