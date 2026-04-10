"""
Gemini API — direct REST, no SDK.
Generates draft tweet only. Retries on 429 with backoff.
"""

import time
import requests
from config import GEMINI_API_KEY

# gemini-1.5-flash: 15 RPM, 1500 RPD on free tier
_ENDPOINT = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-1.5-flash:generateContent"
)


def setup_gemini() -> None:
    if not GEMINI_API_KEY:
        print("[gemini] WARNING: GEMINI_API_KEY not set.")
    else:
        print(f"[gemini] ready (key ends ...{GEMINI_API_KEY[-6:]})")


def generate_draft_tweet(article: dict) -> str | None:
    """
    Ask Gemini to write a punchy draft tweet.
    Retries up to 3 times on 429 with exponential backoff.
    Returns tweet string or None on failure.
    """
    if not GEMINI_API_KEY:
        return None

    prompt = (
        f"Write a single tweet under 220 characters about this Indian news story.\n"
        f"Title: {article['title']}\n"
        f"Context: {article.get('description', '')[:300]}\n\n"
        f"Rules: present tense, punchy opening, no hashtags, no emojis, "
        f"no 'BREAKING', sound like a smart informed Indian observer.\n"
        f"Reply with ONLY the tweet text, nothing else."
    )

    payload = {
        "contents":         [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 100},
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                _ENDPOINT,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=25,
            )

            if resp.status_code == 429:
                wait = 5 * (2 ** attempt)   # 5s → 10s → 20s
                print(f"  [gemini] 429 rate limit — waiting {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
                continue

            if not resp.ok:
                print(f"  [gemini] HTTP {resp.status_code}: {resp.text[:200]}")
                return None

            tweet = (
                resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                .strip().strip('"')
            )
            return tweet[:220] if tweet else None

        except Exception as exc:
            print(f"  [gemini] error: {exc}")
            return None

    print("  [gemini] all retries exhausted")
    return None
