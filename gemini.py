"""
Gemini API — direct REST, no SDK.
Only generates the draft tweet; RSS description is used as the summary.
"""

import requests
from config import GEMINI_API_KEY

# Try both v1 and v1beta — some models only live on one
_ENDPOINTS = [
    "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
]


def setup_gemini() -> None:
    if not GEMINI_API_KEY:
        print("[gemini] WARNING: GEMINI_API_KEY not set.")
    else:
        print(f"[gemini] key loaded (ends ...{GEMINI_API_KEY[-6:]})")


def generate_draft_tweet(article: dict) -> str | None:
    """
    Ask Gemini to write a single punchy draft tweet based on the article.
    Returns the tweet string, or None on failure.
    """
    if not GEMINI_API_KEY:
        return None

    prompt = (
        f"Write a single tweet under 220 characters about this Indian news story.\n"
        f"Title: {article['title']}\n"
        f"Summary: {article.get('description', '')[:300]}\n\n"
        f"Rules: present tense, punchy opening, no hashtags, no emojis, "
        f"no 'BREAKING', sound like a smart informed Indian observer.\n"
        f"Reply with ONLY the tweet text, nothing else."
    )

    payload = {
        "contents":         [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 120},
    }

    for endpoint in _ENDPOINTS:
        try:
            resp = requests.post(
                endpoint,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=25,
            )

            if not resp.ok:
                print(f"  [gemini] {endpoint.split('/v')[1][:10]} → "
                      f"HTTP {resp.status_code}: {resp.text[:200]}")
                continue

            tweet = (
                resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                .strip().strip('"')
            )
            return tweet[:220] if tweet else None

        except Exception as exc:
            print(f"  [gemini] error on {endpoint}: {exc}")
            continue

    return None
