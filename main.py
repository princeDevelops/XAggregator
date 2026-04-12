"""
XAggregator — entry point.

Flow (every 30 min via GitHub Actions):
  1. Fetch all articles across every category
  2. Detect trending stories (3+ sources same story) → send TRENDING alerts first
  3. Process each category normally → send individual articles
"""

import time

from config      import CATEGORIES, MAX_ARTICLES_PER_CATEGORY, MIN_KEYWORD_SCORE, WATCHLIST
from db          import init_db, is_seen, mark_seen
from fetcher     import fetch_category_articles, scrape_article_meta, is_india_relevant
from discord_bot import send_article, send_trending, send_run_summary, send_failure_alert, send_watchlist_alert
from trending    import detect_trending
from api_fetcher import fetch_all_api_news
from caption     import generate_caption


def _check_watchlist(article: dict) -> None:
    """Fire a watchlist alert if the article matches any watched keyword."""
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    for keyword in WATCHLIST:
        if keyword.lower() in text:
            send_watchlist_alert(article, keyword)
            break   # one alert per article is enough


def _enrich(article: dict) -> None:
    """
    Scrape the real article page for image and body content.
    Always scrapes for body — replaces short RSS descriptions with full article text.
    """
    needs_image = not article.get("image")
    needs_desc  = len(article.get("description", "")) < 400   # scrape if we don't already have a rich body
    if needs_image or needs_desc:
        meta = scrape_article_meta(article["url"])
        if needs_image and meta["image"]:
            article["image"] = meta["image"]
        if meta["description"] and len(meta["description"]) > len(article.get("description", "")):
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
        article["caption"] = generate_caption(article)

        webhook_key = category.get("webhook")
        ok = send_article(article, webhook_key=webhook_key)
        if ok:
            mark_seen(article["url"], article["title"])
            _check_watchlist(article)
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

    # ── Step 4: API news (NewsAPI + GNews + Currents → separate channel) ────────
    print("\n[fetching API news...]")
    api_sent = 0
    for article in fetch_all_api_news():
        if is_seen(article["url"]):
            continue
        _enrich(article)
        article["caption"] = generate_caption(article)
        ok = send_article(article, webhook_key="API_NEWS_WEBHOOK_URL")
        if ok:
            mark_seen(article["url"], article["title"])
            _check_watchlist(article)
            api_sent += 1
            print(f"  ✓ [API NEWS] {article['title'][:80]}")
        else:
            print(f"  ✗ [API NEWS] failed to send")
        time.sleep(1.2)
    print(f"  → {api_sent} article(s) sent for API NEWS")
    counts["API NEWS"] = api_sent

    # ── Step 5: run summary + failure alert ───────────────────────────────────
    total_sent = sum(counts.values())
    if total_sent == 0:
        send_failure_alert()
    send_run_summary(counts, trending_count=len(trending_stories))

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
