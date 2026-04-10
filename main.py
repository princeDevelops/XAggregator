"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  For each category (priority order):
    1. Fetch & score articles from RSS feeds
    2. Skip already-seen URLs (SQLite)
    3. Skip if no India keyword in title (hard gate)
    4. Scrape real article page → fill missing image + description in one call
    5. Call Gemini for draft tweet (if daily budget remains)
    6. Send to Discord
    7. Mark URL as seen
"""

import time

from config      import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE
from db          import init_db, is_seen, mark_seen, get_daily_usage, increment_usage
from fetcher     import fetch_category_articles, scrape_article_meta, is_india_relevant
from gemini      import setup_gemini, generate_draft_tweet
from discord_bot import send_article

# Gemini free tier = 15 requests/minute → must wait ≥4s between calls
_GEMINI_DELAY = 5


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

        # Scrape real article page if we're missing image or description.
        # One HTTP call returns both — handles Google News redirect URLs too.
        needs_image = not article.get("image")
        needs_desc  = len(article.get("description", "")) < 80

        if needs_image or needs_desc:
            meta = scrape_article_meta(article["url"])
            if needs_image and meta["image"]:
                article["image"] = meta["image"]
            if needs_desc and meta["description"]:
                article["description"] = meta["description"]

        # Gemini — draft tweet only
        draft_tweet = None
        if get_daily_usage(name) < budget:
            draft_tweet = generate_draft_tweet(article)
            if draft_tweet:
                increment_usage(name)
                time.sleep(_GEMINI_DELAY)   # respect 15 RPM free tier limit

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
