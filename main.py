"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  1. Fetch all articles across every category
  2. Detect trending stories (3+ sources same story) → send TRENDING alerts first
  3. Process each category normally → send individual articles
"""

import time

from config      import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE
from db          import init_db, is_seen, mark_seen
from fetcher     import fetch_category_articles, scrape_article_meta, is_india_relevant
from discord_bot import send_article, send_trending, send_run_summary
from trending    import detect_trending


def _enrich(article: dict) -> None:
    """Fill missing image / description by scraping the real article page."""
    needs_image = not article.get("image")
    needs_desc  = len(article.get("description", "")) < 80
    if needs_image or needs_desc:
        meta = scrape_article_meta(article["url"])
        if needs_image and meta["image"]:
            article["image"] = meta["image"]
        if needs_desc and meta["description"]:
            article["description"] = meta["description"]


def process_category(category: dict, prefetched: list[dict]) -> int:
    """Send up to MAX_ARTICLES_PER_CATEGORY unseen articles for this category."""
    name = category["name"]
    sent = 0

    skip_filters = category.get("skip_filters", False)

    for article in prefetched:
        if sent >= MAX_ARTICLES_PER_CATEGORY:
            break
        if not skip_filters:
            if article["score"] < MIN_KEYWORD_SCORE:
                continue
            if not is_india_relevant(article):
                continue
        if is_seen(article["url"]):
            continue

        _enrich(article)

        webhook_key = category.get("webhook")
        ok = send_article(article, webhook_key=webhook_key)
        if ok:
            mark_seen(article["url"], article["title"])
            sent += 1
            print(f"  ✓ [{name}] {article['title'][:80]}")
        else:
            print(f"  ✗ [{name}] failed to send")

        time.sleep(1.2)

    print(f"  → {sent} article(s) sent for {name}")
    return sent


def main() -> None:
    print("=" * 60)
    print("XAggregator starting")
    print("=" * 60)

    init_db()

    # ── Step 1: fetch all articles across every category ──────────────────────
    print("\n[fetching all feeds...]")
    category_articles: dict[str, list[dict]] = {}
    all_articles: list[dict] = []

    for category in CATEGORIES:
        articles = fetch_category_articles(category)
        fresh = [
            a for a in articles
            if a["score"] >= MIN_KEYWORD_SCORE
            and is_india_relevant(a)
            and not is_seen(a["url"])
        ]
        category_articles[category["name"]] = articles
        all_articles.extend(fresh)
        print(f"  [{category['name']}] fetched={len(articles)} fresh={len(fresh)}")

    # ── Step 2: detect trending stories ───────────────────────────────────────
    trending_stories = detect_trending(all_articles)

    if trending_stories:
        print(f"\n[🔴 TRENDING — {len(trending_stories)} story(s) detected]")
        for story in trending_stories:
            rep = story["representative"]
            _enrich(rep)
            ok = send_trending(story)
            if ok:
                print(f"  🔴 TRENDING [{story['count']} sources] {rep['title'][:70]}")
            time.sleep(1.2)
    else:
        print("\n[no trending stories this run]")

    # ── Step 3: process categories normally ───────────────────────────────────
    counts: dict[str, int] = {}
    for category in CATEGORIES:
        print(f"\n[{category['priority']}] {category['name']}")
        sent = process_category(category, category_articles[category["name"]])
        counts[category["name"]] = sent
        time.sleep(2)

    # ── Step 4: run summary ────────────────────────────────────────────────────
    send_run_summary(counts, trending_count=len(trending_stories))

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
