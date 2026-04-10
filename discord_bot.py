"""
Discord webhook integration.
Summary = RSS description (always present).
Draft tweet = Gemini output (when available).
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


def _build_embed(article: dict, draft_tweet: str | None) -> dict:
    category = article["category"]
    emoji    = EMOJIS.get(category, "📰")
    color    = COLORS.get(category, 0x808080)
    now_utc  = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # RSS description is always the summary — no API needed
    parts = []
    if article.get("description"):
        parts.append(article["description"])

    if draft_tweet:
        parts.append(f"**📝 Draft tweet:**\n{draft_tweet}")

    description = "\n\n".join(parts) if parts else "*No description available.*"

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

    return embed


def send_article(article: dict, draft_tweet: str | None) -> bool:
    embed   = _build_embed(article, draft_tweet)
    payload = {"embeds": [embed]}

    for attempt in range(2):
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code == 429:
                retry_after = resp.json().get("retry_after", 2)
                print(f"  [discord] rate-limited, waiting {retry_after}s")
                time.sleep(float(retry_after) + 0.5)
                continue
            resp.raise_for_status()
            return True
        except Exception as exc:
            print(f"  [discord] error (attempt {attempt + 1}): {exc}")
            time.sleep(1)

    return False
