"""CRUD operations for the BrushUp database."""

from __future__ import annotations
from .database import get_connection


# --- Problems ---

def upsert_problem(slug: str, title: str, num: int, difficulty: str, category: str = ""):
    """Insert or update a problem's core info."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO problems (slug, title, num, difficulty, category) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(slug) DO UPDATE SET title=excluded.title, num=excluded.num, "
        "difficulty=excluded.difficulty, category=excluded.category",
        (slug, title, num, difficulty, category),
    )
    conn.commit()
    conn.close()


def get_problem(slug: str) -> dict | None:
    """Get a single problem by slug. Returns dict or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM problems WHERE slug=?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_problems() -> list[dict]:
    """Get all problems."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM problems ORDER BY num").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_note(slug: str, note: str):
    conn = get_connection()
    conn.execute("UPDATE problems SET notes=? WHERE slug=?", (note, slug))
    conn.commit()
    conn.close()


def set_must_repeat(slug: str, val: bool):
    conn = get_connection()
    conn.execute("UPDATE problems SET must_repeat=? WHERE slug=?", (int(val), slug))
    conn.commit()
    conn.close()


def set_solution_viewed(slug: str, val: bool):
    conn = get_connection()
    conn.execute("UPDATE problems SET solution_viewed=? WHERE slug=?", (int(val), slug))
    conn.commit()
    conn.close()


def get_all_problem_data() -> dict:
    """Return all problem metadata keyed by slug, for frontend compatibility.

    Returns dict matching the old problem_data.json format:
    {slug: {notes, must_repeat, solution_viewed, ai_reviews, time_spent}}
    """
    conn = get_connection()
    problems = conn.execute("SELECT slug, notes, must_repeat, solution_viewed FROM problems").fetchall()
    reviews = conn.execute("SELECT slug, round, date, analysis FROM ai_reviews ORDER BY id").fetchall()
    times = conn.execute("SELECT slug, seconds FROM time_records ORDER BY id").fetchall()
    conn.close()

    result = {}
    for p in problems:
        result[p["slug"]] = {
            "notes": p["notes"] or "",
            "must_repeat": bool(p["must_repeat"]),
            "solution_viewed": bool(p["solution_viewed"]),
            "ai_reviews": [],
            "time_spent": [],
        }
    for r in reviews:
        if r["slug"] in result:
            result[r["slug"]]["ai_reviews"].append({
                "round": r["round"], "date": r["date"], "analysis": r["analysis"],
            })
    for t in times:
        if t["slug"] in result:
            result[t["slug"]]["time_spent"].append(t["seconds"])
    return result


# --- Progress ---

def upsert_progress(slug: str, round_key: str, completed_date: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO progress (slug, round, completed_date) VALUES (?, ?, ?) "
        "ON CONFLICT(slug, round) DO UPDATE SET completed_date=excluded.completed_date",
        (slug, round_key, completed_date),
    )
    conn.commit()
    conn.close()


def get_progress(slug: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT round, completed_date FROM progress WHERE slug=? ORDER BY round", (slug,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- AI Reviews ---

def add_ai_review(slug: str, round_key: str, date_str: str, analysis: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO ai_reviews (slug, round, date, analysis) VALUES (?, ?, ?, ?)",
        (slug, round_key.upper(), date_str, analysis),
    )
    conn.commit()
    conn.close()


def get_ai_reviews(slug: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT round, date, analysis FROM ai_reviews WHERE slug=? ORDER BY id", (slug,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Time Records ---

def add_time_record(slug: str, seconds: int):
    conn = get_connection()
    conn.execute("INSERT INTO time_records (slug, seconds) VALUES (?, ?)", (slug, seconds))
    conn.commit()
    conn.close()


# --- Checkins ---

def upsert_checkin(date_str: str, day_num: int, new_count: int, review_count: int,
                   total: int, new_problems: str, review_problems: str, struggles: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO checkins (date, day_num, new_count, review_count, total, new_problems, review_problems, struggles) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(date) DO UPDATE SET "
        "day_num=excluded.day_num, new_count=excluded.new_count, review_count=excluded.review_count, "
        "total=excluded.total, new_problems=excluded.new_problems, review_problems=excluded.review_problems, "
        "struggles=excluded.struggles",
        (date_str, day_num, new_count, review_count, total, new_problems, review_problems, struggles),
    )
    conn.commit()
    conn.close()


# --- Config ---

def get_config(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_config(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()
