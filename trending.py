"""
Trending story detector.
Groups articles by title similarity across all sources.
A story is TRENDING if 3+ different sources cover it in the same run.
"""

import re

# words too common to use for comparison
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "has", "have", "had", "be", "been", "will", "would", "can", "could",
    "says", "said", "after", "over", "into", "its", "his", "her", "their",
    "this", "that", "as", "it", "he", "she", "they", "we", "you", "i",
    "new", "news", "report", "says", "amid", "after", "before", "latest",
}

TRENDING_THRESHOLD = 3   # min sources covering same story to flag as trending


def _significant_words(title: str) -> set[str]:
    """Extract meaningful words from a title for comparison."""
    words = re.findall(r"[a-zA-Z]+", title.lower())
    return {w for w in words if len(w) >= 4 and w not in _STOPWORDS}


def _similarity(title_a: str, title_b: str) -> float:
    """
    Jaccard similarity between significant word sets.
    Returns 0.0–1.0. Above 0.35 = same story.
    """
    words_a = _significant_words(title_a)
    words_b = _significant_words(title_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union        = words_a | words_b
    return len(intersection) / len(union)


def detect_trending(articles: list[dict]) -> list[dict]:
    """
    Given a flat list of articles from all categories/sources,
    find stories covered by TRENDING_THRESHOLD+ different sources.

    Returns a list of trending story dicts:
    {
        "representative": article dict (highest scored),
        "sources":        ["NDTV", "Reuters", "ANI", ...],
        "count":          4,
        "category":       "INDIA",
    }
    """
    # group articles by story cluster
    clusters: list[list[dict]] = []

    for article in articles:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            if _similarity(article["title"], rep["title"]) >= 0.45:
                cluster.append(article)
                placed = True
                break
        if not placed:
            clusters.append([article])

    trending = []
    for cluster in clusters:
        # count unique sources
        sources = list({a["source"] for a in cluster})
        if len(sources) < TRENDING_THRESHOLD:
            continue

        # pick best representative: highest score, prefer known outlets
        rep = max(cluster, key=lambda a: a["score"])

        trending.append({
            "representative": rep,
            "sources":        sources,
            "count":          len(sources),
            "category":       rep["category"],
        })

    # sort by source count descending
    trending.sort(key=lambda t: t["count"], reverse=True)
    return trending
