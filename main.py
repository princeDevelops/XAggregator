"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  For each category (priority order):
    1. Fetch & score articles from RSS feeds
    2. Skip already-seen URLs (SQLite)
    3. Scrape og:image if RSS didn't include one
    4. Call Gemini (if daily budget remains) → summary + draft tweet
    5. Send to Discord as a rich embed
    6. Mark URL as seen
"""

import time

from config import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE
from db     import init_db, is_seen, mark_seen, get_daily_usage, increment_usage
from fetcher     import fetch_category_articles, scrape_og_image
from gemini      import setup_gemini, generate_content
from discord_bot import send_article


def process_category(category: dict) -> None:
    name     = category["name"]
    budget   = category["gemini_budget"]
    articles = fetch_category_articles(category)

    sent = 0
    for article in articles:
        if sent >= MAX_ARTICLES_PER_CATEGORY:
            break

        if article["score"] < MIN_KEYWORD_SCORE:
            continue

        if is_seen(article["url"]):
            continue

        # fetch image if RSS didn't provide one
        if not article.get("image"):
            article["image"] = scrape_og_image(article["url"])

        # Gemini — respect daily budget
        ai_content = None
        if get_daily_usage(name) < budget:
            ai_content = generate_content(article)
            if ai_content:
                increment_usage(name)

        ok = send_article(article, ai_content)
        if ok:
            mark_seen(article["url"], article["title"])
            sent += 1
            print(f"  ✓ [{name}] {article['title'][:80]}")
        else:
            print(f"  ✗ [{name}] failed to send — skipping")

        time.sleep(1.2)   # stay well under Discord's 5 req/2 s webhook limit

    print(f"  → {sent} article(s) sent for {name}")


def main() -> None:
    print("=" * 60)
    print("XAggregator starting")
    print("=" * 60)

    init_db()
    setup_gemini()

    for category in CATEGORIES:
        print(f"\n[{category['priority']}] {category['name']}")
        process_category(category)
        time.sleep(2)   # small gap between categories

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
