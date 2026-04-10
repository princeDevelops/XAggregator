"""
Gemini API — direct REST calls via requests.
No SDK dependency, works with any valid API key.
"""

import re
import requests
from config import GEMINI_API_KEY

_API_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.0-flash:generateContent"
)


def setup_gemini() -> None:
    if not GEMINI_API_KEY:
        print("[gemini] WARNING: GEMINI_API_KEY not set — summaries will be skipped.")
    else:
        print("[gemini] API key loaded.")


def generate_content(article: dict) -> dict | None:
    """
    Call Gemini REST API and return:
        { "summary": "...", "draft_tweet": "..." }
    Returns None on any failure.
    """
    if not GEMINI_API_KEY:
        return None

    prompt = f"""You are a sharp, concise Indian news analyst writing for an audience on X (Twitter).

Article details:
  Title:       {article['title']}
  Description: {article.get('description', 'N/A')}
  Source:      {article.get('source', 'N/A')}

Produce two things:

SUMMARY:
Write 3-4 sentences. Cover what happened, why it matters for India, and what comes next.
Be specific — no vague filler. Plain English.

DRAFT_TWEET:
Write a single tweet under 220 characters.
- Open with a punchy statement (not a question).
- Present tense. Sound like a smart informed person, not a bot.
- No hashtags. No emojis. No "BREAKING".

Reply in this exact format and nothing else:
SUMMARY: <your summary here>
DRAFT_TWEET: <your tweet here>"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }

    try:
        resp = requests.post(
            _API_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()

        text = (
            resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        )

        summary_match = re.search(r"SUMMARY:\s*(.*?)(?=\nDRAFT_TWEET:|$)", text, re.DOTALL)
        tweet_match   = re.search(r"DRAFT_TWEET:\s*(.*?)$",                 text, re.DOTALL)

        summary     = summary_match.group(1).strip() if summary_match else ""
        draft_tweet = tweet_match.group(1).strip()   if tweet_match   else ""

        if not summary and not draft_tweet:
            return None

        return {"summary": summary, "draft_tweet": draft_tweet}

    except Exception as exc:
        print(f"  [gemini] error: {exc}")
        return None
