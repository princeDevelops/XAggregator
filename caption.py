"""
Instagram caption generator — no LLM required.

Strategy:
  1. First sentence of og:description as the caption body
  2. spaCy named-entity extraction for hashtags (PERSON, ORG, GPE, LOC, NORP)
  3. Fixed hashtags appended based on article category
  4. Graceful fallback to title-only if spaCy model is unavailable
"""

import re

# ── spaCy lazy loader ─────────────────────────────────────────────────────────

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = False   # mark as unavailable so we don't retry
    return _nlp if _nlp is not False else None


# ── Category → fixed hashtags ─────────────────────────────────────────────────

_CATEGORY_TAGS = {
    "INDIA":               ["#India", "#IndiaNews", "#Bharat"],
    "GEOPOLITICS & WARS":  ["#India", "#Geopolitics", "#WorldNews"],
    "POLITICS":            ["#India", "#IndianPolitics", "#Politics"],
    "SCANDALS & OUTRAGES": ["#India", "#Breaking", "#Controversy"],
    "ECONOMY":             ["#India", "#IndianEconomy", "#Business"],
    "GOVT & POLICY":       ["#India", "#Policy", "#Governance"],
    "GOOGLE ALERTS":       ["#India", "#IndiaNews"],
    "API NEWS":            ["#India", "#IndiaNews"],
    "HINDU-MUSLIM":        ["#India", "#CommunalNews", "#HinduMuslim"],
    "VIDEO":               ["#India", "#IndiaNews", "#Watch"],
    "PAKISTAN":            ["#Pakistan", "#PakistanNews", "#IndoPak"],
}


# ── Core functions ─────────────────────────────────────────────────────────────

def generate_hashtags(article: dict) -> list[str]:
    """
    Extract named entities from title + description and return hashtag list.
    Falls back to category-only hashtags if spaCy is unavailable.
    """
    tags: list[str] = list(_CATEGORY_TAGS.get(article.get("category", ""), ["#India", "#IndiaNews"]))

    nlp = _get_nlp()
    if nlp is None:
        return tags

    text = f"{article.get('title', '')} {article.get('description', '')}"
    doc  = nlp(text[:1000])   # cap input to keep it fast

    seen: set[str] = set(t.lower() for t in tags)
    for ent in doc.ents:
        if ent.label_ not in ("PERSON", "ORG", "GPE", "LOC", "NORP"):
            continue
        # clean: remove spaces/special chars, title-case
        tag_text = re.sub(r"[^a-zA-Z0-9]", "", ent.text.title())
        if len(tag_text) < 3:
            continue
        tag = f"#{tag_text}"
        if tag.lower() not in seen:
            seen.add(tag.lower())
            tags.append(tag)

    return tags[:15]   # Instagram recommends ≤ 15 targeted hashtags


def generate_caption(article: dict) -> str:
    """
    Build a ready-to-post Instagram caption:
      <first sentence of description>
      <blank line>
      <hashtags>
    """
    desc = article.get("description", "").strip()

    if desc:
        # split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r"(?<=[.!?])\s+", desc)
        body = sentences[0].strip()
        if len(body) > 220:
            body = body[:220].rsplit(" ", 1)[0] + "…"
    else:
        body = article.get("title", "").strip()

    hashtags = generate_hashtags(article)
    return f"{body}\n\n{' '.join(hashtags)}"
