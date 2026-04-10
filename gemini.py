"""
Gemini API integration.
Generates a 3-4 line summary and a ready-to-post draft tweet for each article.
"""

import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL


def setup_gemini() -> None:
    genai.configure(api_key=GEMINI_API_KEY)


def generate_content(article: dict) -> dict | None:
    """
    Call Gemini and return:
        { "summary": "...", "draft_tweet": "..." }
    Returns None if the call fails.
    """
    try:
        model  = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""You are a sharp, concise news analyst writing for an informed audience on X (Twitter).

Article details:
  Title:       {article['title']}
  Description: {article.get('description', 'N/A')}
  Source:      {article.get('source', 'N/A')}

Produce two things:

SUMMARY:
Write 3-4 sentences. Cover what happened, why it matters, and what comes next.
Be specific — no vague filler. Use plain English.

DRAFT_TWEET:
Write a single tweet under 220 characters.
- Open with a punchy statement (not a question).
- Use present tense.
- Sound like a smart human, not a bot.
- No hashtags. No emojis. No "BREAKING".

Reply in this exact format (nothing else):
SUMMARY: <your summary here>
DRAFT_TWEET: <your tweet here>"""

        response = model.generate_content(prompt)
        text     = response.text.strip()

        summary_match = re.search(
            r"SUMMARY:\s*(.*?)(?=\nDRAFT_TWEET:|$)", text, re.DOTALL
        )
        tweet_match = re.search(
            r"DRAFT_TWEET:\s*(.*?)$", text, re.DOTALL
        )

        summary     = summary_match.group(1).strip() if summary_match else ""
        draft_tweet = tweet_match.group(1).strip()   if tweet_match   else ""

        if not summary and not draft_tweet:
            return None

        return {"summary": summary, "draft_tweet": draft_tweet}

    except Exception as exc:
        print(f"  [gemini] error: {exc}")
        return None
