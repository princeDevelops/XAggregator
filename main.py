"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  For each category (priority order):
    1. Fetch & score articles from RSS feeds
    2. Skip already-seen URLs (SQLite)
    3. Skip if no India keyword in title (hard gate)
    4. Resolve real URL → scrape og:image
    5. Call Gemini for draft tweet (if daily budget remains)
    6. Send to Discord: RSS description as summary + draft tweet
    7. Mark URL as seen
"""

import time

from config      import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE
from db          import init_db, is_seen, mark_seen, get_daily_usage, increment_usage
from fetcher     import fetch_category_articles, scrape_og_image, is_india_relevant
from gemini      import setup_gemini, generate_draft_tweet
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

        if not is_india_relevant(article):
            continue

        if is_seen(article["url"]):
            continue

        # scrape og:image if RSS didn't provide one
        # (fetcher resolves Google News redirect URLs automatically)
        if not article.get("image"):
            article["image"] = scrape_og_image(article["url"])

        # Gemini — draft tweet only, RSS description is the summary
        draft_tweet = None
        if get_daily_usage(name) < budget:
            draft_tweet = generate_draft_tweet(article)
            if draft_tweet:
                increment_usage(name)

        ok = send_article(article, draft_tweet)
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
    setup_gemini()

    for category in CATEGORIES:
        print(f"\n[{category['priority']}] {category['name']}")
        process_category(category)
        time.sleep(2)

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
