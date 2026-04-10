"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  For each category (priority order):
    1. Fetch & score articles from RSS feeds
    2. Skip already-seen URLs (SQLite)
    3. Skip if no India keyword in title
    4. Fill missing image / description by scraping real article page
    5. Send to Discord
    6. Mark URL as seen
"""

import time

from config      import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE
from db          import init_db, is_seen, mark_seen
from fetcher     import fetch_category_articles, scrape_article_meta, is_india_relevant
from discord_bot import send_article


def process_category(category: dict) -> None:
    name     = category["name"]
    articles = fetch_category_articles(category)

    sent = 0
    for article in articles:
        if sent >= MAX_ARTICLES_PER_CATEGORY:
            break
        if article["score"] < MIN_KEYWORD_SCORE:
            continue
        if not is_india_relevant(article):
            continue
        if is_seen(article["url"]):
            continue

        # If image or description is missing/thin, scrape the real article page.
        # _decode_gnews_url handles Google News redirect URLs automatically.
        needs_image = not article.get("image")
        needs_desc  = len(article.get("description", "")) < 80

        if needs_image or needs_desc:
            meta = scrape_article_meta(article["url"])
            if needs_image and meta["image"]:
                article["image"] = meta["image"]
            if needs_desc and meta["description"]:
                article["description"] = meta["description"]

        ok = send_article(article)
        if ok:
            mark_seen(article["url"], article["title"])
            sent += 1
            print(f"  ✓ [{name}] {article['title'][:80]}")
        else:
            print(f"  ✗ [{name}] failed to send")

        time.sleep(1.2)

    print(f"  → {sent} article(s) sent for {name}")


def main() -> None:
    print("=" * 60)
    print("XAggregator starting")
    print("=" * 60)

    init_db()

    for category in CATEGORIES:
        print(f"\n[{category['priority']}] {category['name']}")
        process_category(category)
        time.sleep(2)

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
