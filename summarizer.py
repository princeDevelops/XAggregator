"""
Article summarizer using Groq (free tier Llama 3).
Condenses long article bodies to 2-3 sentences for Discord embeds.
Falls back gracefully when GROQ_API_KEY is not set or on any API error.
"""

import requests
from config import GROQ_API_KEY

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL    = "llama-3.3-70b-versatile"
_MIN_LEN  = 200   # don't bother summarizing already-short descriptions


def summarize_article(title: str, body: str) -> str | None:
    """
    Summarize an article to 2-3 concise sentences using Groq.
    Returns None if the key is missing, the body is too short, or on any error.
    The caller should keep the original description if None is returned.
    """
    if not GROQ_API_KEY or len(body) < _MIN_LEN:
        return None

    prompt = (
        "Summarize this news article in 2-3 concise, factual sentences. "
        "Cover the key facts only (who, what, where, outcome). "
        "No commentary, no opinion, no filler phrases like 'The article says' or 'According to'.\n\n"
        f"Title: {title}\n\n"
        f"Article: {body[:3000]}"
    )

    try:
        resp = requests.post(
            _GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model":       _MODEL,
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  160,
                "temperature": 0.2,
            },
            timeout=20,
        )
        if resp.status_code == 429:
            print("  [groq] rate-limited — skipping summary this article")
            return None
        resp.raise_for_status()
        summary = resp.json()["choices"][0]["message"]["content"].strip()
        return summary if len(summary) > 40 else None
    except Exception as exc:
        print(f"  [groq] summarize error: {exc}")
        return None
