"""One-time migration from JSON/Markdown data files to SQLite."""

from __future__ import annotations

import re

from .database import get_connection
from .queries import get_config, set_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_round_done(val: str) -> bool:
    """A round is done if value is non-empty and not the placeholder dash."""
    return bool(val) and val not in ("", "—")


# ---------------------------------------------------------------------------
# Migration steps
# ---------------------------------------------------------------------------

def _migrate_progress_table(conn) -> set[str]:
    """Parse progress Markdown and populate problems + progress tables.

    Returns the set of slugs inserted into problems.
    """
    from ..config import PROGRESS_FILE
    from ..progress import parse_progress_table
    from ..config import get_round_keys

    if not PROGRESS_FILE.exists():
        return set()

    round_keys = get_round_keys()
    _, rows = parse_progress_table(PROGRESS_FILE)

    problem_rows = []
    progress_rows = []

    for row in rows:
        slug = row.get("title_slug", "")
        if not slug:
            continue

        raw_title = row.get("title", "")
        title_match = re.search(r"\[(.+?)\]", raw_title)
        title = title_match.group(1) if title_match else raw_title

        try:
            num = int(row.get("seq", 0))
        except (ValueError, TypeError):
            num = 0

        difficulty = row.get("difficulty", "")
        problem_rows.append((slug, title, num, difficulty))

        for rk in round_keys:
            val = row.get(rk, "")
            if _is_round_done(val):
                progress_rows.append((slug, rk, val))

    conn.executemany(
        "INSERT INTO problems (slug, title, num, difficulty) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(slug) DO UPDATE SET title=excluded.title, num=excluded.num, "
        "difficulty=excluded.difficulty",
        problem_rows,
    )

    conn.executemany(
        "INSERT INTO progress (slug, round, completed_date) VALUES (?, ?, ?) "
        "ON CONFLICT(slug, round) DO UPDATE SET completed_date=excluded.completed_date",
        progress_rows,
    )

    return {r[0] for r in problem_rows}


def _migrate_categories(conn):
    """Update problems.category from SLUG_CATEGORY dict."""
    from ..init_plan import SLUG_CATEGORY

    rows = [(category, slug) for slug, category in SLUG_CATEGORY.items()]
    conn.executemany(
        "UPDATE problems SET category=? WHERE slug=?",
        rows,
    )


def _migrate_problem_metadata(conn):
    """Load problem_data.json and update problems, ai_reviews, time_records tables."""
    from ..config import PLAN_DIR
    from ..storage import load_json

    json_path = PLAN_DIR / "problem_data.json"
    data = load_json(json_path)
    if not data or not isinstance(data, dict):
        return

    problem_updates = []
    ai_review_rows = []
    time_record_rows = []

    for slug, meta in data.items():
        if not isinstance(meta, dict):
            continue

        notes = meta.get("notes", "") or ""
        solution_viewed = int(bool(meta.get("solution_viewed", False)))
        must_repeat = int(bool(meta.get("must_repeat", False)))
        problem_updates.append((notes, solution_viewed, must_repeat, slug))

        for review in meta.get("ai_reviews", []):
            if not isinstance(review, dict):
                continue
            round_key = str(review.get("round", "")).upper()
            date_str = str(review.get("date", ""))
            analysis = str(review.get("analysis", ""))
            if round_key and date_str and analysis:
                ai_review_rows.append((slug, round_key, date_str, analysis))

        for seconds in meta.get("time_spent", []):
            try:
                ai_review_rows  # noqa: just a marker
                time_record_rows.append((slug, int(seconds)))
            except (ValueError, TypeError):
                continue

    conn.executemany(
        "UPDATE problems SET notes=?, solution_viewed=?, must_repeat=? WHERE slug=?",
        problem_updates,
    )

    conn.executemany(
        "INSERT INTO ai_reviews (slug, round, date, analysis) VALUES (?, ?, ?, ?)",
        ai_review_rows,
    )

    conn.executemany(
        "INSERT INTO time_records (slug, seconds) VALUES (?, ?)",
        time_record_rows,
    )


def _migrate_checkins(conn):
    """Parse check-in Markdown and populate checkins table."""
    from ..config import CHECKIN_FILE
    from ..features import parse_checkin_data

    entries = parse_checkin_data(CHECKIN_FILE)
    if not entries:
        return

    rows = [
        (
            str(e["date"]),
            0,               # day_num — not stored in the Markdown; default 0
            e.get("new", 0),
            e.get("review", 0),
            e.get("total", 0),
            "",              # new_problems
            "",              # review_problems
            "",              # struggles
        )
        for e in entries
    ]

    conn.executemany(
        "INSERT INTO checkins "
        "(date, day_num, new_count, review_count, total, new_problems, review_problems, struggles) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(date) DO UPDATE SET "
        "new_count=excluded.new_count, review_count=excluded.review_count, "
        "total=excluded.total",
        rows,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _do_migration():
    conn = get_connection()
    try:
        with conn:  # single transaction
            _migrate_progress_table(conn)
            _migrate_categories(conn)
            _migrate_problem_metadata(conn)
            _migrate_checkins(conn)
    finally:
        conn.close()


def migrate_if_needed():
    """Run the one-time data migration unless it has already been completed."""
    if get_config("migration_done") == "1":
        return
    _do_migration()
    set_config("migration_done", "1")
    print("数据迁移完成 ✓")
