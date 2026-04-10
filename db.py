"""
SQLite persistence layer.
Tracks:
  - seen_articles  : prevents duplicate posts across runs
  - gemini_usage   : per-category daily call counter
"""

import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path("data/aggregator.db")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS seen_articles (
                url      TEXT PRIMARY KEY,
                title    TEXT,
                seen_at  TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS gemini_usage (
                date     TEXT NOT NULL,
                category TEXT NOT NULL,
                count    INTEGER DEFAULT 0,
                PRIMARY KEY (date, category)
            );
        """)
        # prune articles older than 7 days to keep DB small
        con.execute("DELETE FROM seen_articles WHERE seen_at < date('now', '-7 days')")


# ── Seen articles ──────────────────────────────────────────────────────────────

def is_seen(url: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM seen_articles WHERE url = ?", (url,)
        ).fetchone()
    return row is not None


def mark_seen(url: str, title: str) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR IGNORE INTO seen_articles (url, title) VALUES (?, ?)",
            (url, title),
        )


# ── Gemini usage ───────────────────────────────────────────────────────────────

def get_daily_usage(category: str) -> int:
    today = date.today().isoformat()
    with _conn() as con:
        row = con.execute(
            "SELECT count FROM gemini_usage WHERE date = ? AND category = ?",
            (today, category),
        ).fetchone()
    return row[0] if row else 0


def increment_usage(category: str) -> None:
    today = date.today().isoformat()
    with _conn() as con:
        con.execute(
            """
            INSERT INTO gemini_usage (date, category, count) VALUES (?, ?, 1)
            ON CONFLICT(date, category) DO UPDATE SET count = count + 1
            """,
            (today, category),
        )
