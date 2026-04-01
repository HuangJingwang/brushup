"""Dashboard data aggregation service.

Ports the _reload_data() and _build_comprehensive_data() logic from web.py.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from datetime import date, timedelta

from ..config import DATA_DIR, load_plan_config, load_push_config
from ..features import ROUND_KEYS, compute_category_stats
from ..init_plan import SLUG_CATEGORY
from ..storage import load_json, save_json
from .session_service import check_session_cached

_TODAY_FOCUS_FILE = DATA_DIR / "today_focus.json"
_TODAY_FOCUS_COUNT = 5


# ---------------------------------------------------------------------------
# Today-focus helpers
# ---------------------------------------------------------------------------

def _load_today_focus_state() -> dict:
    return load_json(_TODAY_FOCUS_FILE, default={})


def _save_today_focus_state(state: dict):
    save_json(_TODAY_FOCUS_FILE, state)


def _pick_today_focus(
    todos: list[dict],
    desired_count: int,
    keep_slugs: list[str] | None = None,
    preferred_category: str = "",
) -> tuple[list[dict], str]:
    """Prefer one category, while keeping today's unfinished picks stable."""
    keep_slugs = keep_slugs or []
    todo_by_slug = {item["slug"]: item for item in todos}
    selected = [todo_by_slug[slug] for slug in keep_slugs if slug in todo_by_slug]
    selected_slugs = {item["slug"] for item in selected}

    grouped: dict[str, list[dict]] = {}
    ordered_categories: list[str] = []
    for item in todos:
        cat = item["category"]
        if cat not in grouped:
            grouped[cat] = []
            ordered_categories.append(cat)
        grouped[cat].append(item)

    if not preferred_category or preferred_category not in grouped:
        if selected:
            preferred_category = selected[0]["category"]
        else:
            for cat in ordered_categories:
                if len(grouped[cat]) >= desired_count:
                    preferred_category = cat
                    break
            if not preferred_category and ordered_categories:
                order_index = {cat: idx for idx, cat in enumerate(ordered_categories)}
                preferred_category = max(
                    ordered_categories,
                    key=lambda cat: (len(grouped[cat]), -order_index[cat]),
                )

    if preferred_category in grouped:
        for item in grouped[preferred_category]:
            if item["slug"] in selected_slugs:
                continue
            selected.append(item)
            selected_slugs.add(item["slug"])
            if len(selected) >= desired_count:
                return selected[:desired_count], preferred_category

    for item in todos:
        if item["slug"] in selected_slugs:
            continue
        selected.append(item)
        selected_slugs.add(item["slug"])
        if len(selected) >= desired_count:
            break

    return selected[:desired_count], preferred_category


def _build_today_focus(todos: list[dict], desired_count: int) -> tuple[list[dict], str]:
    today_str = date.today().isoformat()
    config = load_plan_config()
    state = _load_today_focus_state()
    keep_slugs: list[str] = []
    preferred_category = ""

    if (
        state.get("date") == today_str
        and state.get("problem_list") == config.get("problem_list", "hot100")
    ):
        keep_slugs = state.get("slugs", [])
        preferred_category = state.get("preferred_category", "")

    focus_items, preferred_category = _pick_today_focus(
        todos, desired_count, keep_slugs, preferred_category,
    )
    _save_today_focus_state({
        "date": today_str,
        "problem_list": config.get("problem_list", "hot100"),
        "preferred_category": preferred_category,
        "slugs": [item["slug"] for item in focus_items],
    })
    return focus_items, preferred_category


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------

def _compute_trends(checkin_data: list) -> dict:
    if not checkin_data:
        return {"this_week": 0, "last_week": 0, "this_month": 0, "last_month": 0,
                "avg_daily": 0, "week_change": 0}
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    month_start = today.replace(day=1)
    if month_start.month == 1:
        last_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        last_month_start = month_start.replace(month=month_start.month - 1)

    tw = sum(e["total"] for e in checkin_data if e["date"] >= week_start)
    lw = sum(e["total"] for e in checkin_data if last_week_start <= e["date"] < week_start)
    tm = sum(e["total"] for e in checkin_data if e["date"] >= month_start)
    lm = sum(e["total"] for e in checkin_data if last_month_start <= e["date"] < month_start)

    recent_30 = [e for e in checkin_data if e["date"] >= today - timedelta(days=30)]
    avg = sum(e["total"] for e in recent_30) / max(len(recent_30), 1)
    change = ((tw - lw) / max(lw, 1) * 100) if lw > 0 else 0

    return {
        "this_week": tw, "last_week": lw,
        "this_month": tm, "last_month": lm,
        "avg_daily": round(avg, 1),
        "week_change": round(change),
    }


# ---------------------------------------------------------------------------
# Main data builder
# ---------------------------------------------------------------------------

def _build_comprehensive_data(
    rows: list,
    stats: dict,
    checkin_data: list,
    streak: int,
    total_days: int,
    review_due: list,
    optimizations: list,
    est: str,
) -> dict:
    """Build the full JSON dict that the frontend expects."""
    from ..problem_data import get_all_problem_data

    cat_stats = compute_category_stats(rows)
    categories = []
    for cat_name, cs in sorted(cat_stats.items(), key=lambda x: x[0]):
        pct = int(cs["done_r1"] / cs["total"] * 100) if cs["total"] else 0
        categories.append([cat_name, pct])

    daily = [
        [e["date"].strftime("%m/%d"), e["new"], e["review"]]
        for e in checkin_data[-60:]
    ]
    heatmap_data = [[e["date"].isoformat(), e["total"]] for e in checkin_data]
    per_round = [stats["per_round"][rk] for rk in ROUND_KEYS]
    today_str = date.today().isoformat()
    today_ac = sum(
        1 for row in rows
        if any((row.get(rk) or "").strip() == today_str for rk in ROUND_KEYS)
    )

    # Build progress table rows
    table_rows = []
    for row in rows:
        title_match = re.search(r"\[(.+?)\]", row["title"])
        display_title = title_match.group(1) if title_match else row["title"]
        num_match = re.search(r"\[(\d+)\.", row["title"])
        num = num_match.group(1) if num_match else row["seq"]
        cat = SLUG_CATEGORY.get(row.get("title_slug", ""), "其他")
        table_rows.append({
            "seq": row["seq"],
            "num": num,
            "title": display_title,
            "slug": row.get("title_slug", ""),
            "difficulty": row["difficulty"],
            "category": cat,
            "r1": row["r1"],
            "r2": row["r2"],
            "r3": row["r3"],
            "r4": row["r4"],
            "r5": row["r5"],
            "status": row.get("status", ""),
        })

    # New problems (R1 not done) grouped by category, weaker categories first
    cat_stats = compute_category_stats(rows)
    raw_todo = []
    for row in rows:
        if row["r1"] and row["r1"] not in ("", "\u2014"):
            continue
        title_match = re.search(r"\[(.+?)\]", row["title"])
        display_title = title_match.group(1) if title_match else row["title"]
        cat = SLUG_CATEGORY.get(row.get("title_slug", ""), "其他")
        raw_todo.append({
            "title": display_title,
            "slug": row.get("title_slug", ""),
            "difficulty": row["difficulty"],
            "category": cat,
        })

    diff_order = {"简单": 0, "中等": 1, "困难": 2}

    def _cat_priority(cat_name):
        cs = cat_stats.get(cat_name, {})
        total = cs.get("total", 1)
        done = cs.get("done_r1", 0)
        return done / max(total, 1)

    sorted_cats = sorted(set(t["category"] for t in raw_todo), key=_cat_priority)
    cat_groups = OrderedDict((c, []) for c in sorted_cats)
    for t in raw_todo:
        cat_groups[t["category"]].append(t)
    for items in cat_groups.values():
        items.sort(key=lambda x: diff_order.get(x["difficulty"], 1))
    new_todo = []
    for items in cat_groups.values():
        new_todo.extend(items)
    today_focus, today_focus_category = _build_today_focus(new_todo, _TODAY_FOCUS_COUNT)

    # Build checkin records
    checkins = []
    for e in reversed(checkin_data):
        checkins.append({
            "date": e["date"].isoformat(),
            "new": e.get("new", 0),
            "review": e.get("review", 0),
            "total": e.get("total", 0),
        })

    return {
        "total": stats["total"],
        "started_problems": stats["per_round"].get("r1", 0),
        "total_rounds": stats["total_rounds"],
        "done_rounds": stats["done_rounds"],
        "done_problems": stats["done_problems"],
        "today_ac": today_ac,
        "rate": round(stats["rate"], 1),
        "per_round": per_round,
        "streak": streak,
        "total_days": total_days,
        "est": est,
        "categories": categories,
        "daily": daily,
        "heatmap_data": heatmap_data,
        "rows": table_rows,
        "checkins": checkins,
        "review_due": [
            {k: (v.isoformat() if isinstance(v, date) else v) for k, v in r.items()}
            for r in review_due
        ],
        "new_todo": new_todo,
        "today_focus": today_focus,
        "today_focus_category": today_focus_category,
        "today_focus_target": _TODAY_FOCUS_COUNT,
        "plan_config": load_plan_config(),
        "ai_usage": __import__('leetcode_auto.ai_analyzer', fromlist=['get_ai_usage']).get_ai_usage(),
        "user_profile": __import__('leetcode_auto.leetcode_api', fromlist=['load_user_profile']).load_user_profile(),
        "struggles": __import__('leetcode_auto.leetcode_api', fromlist=['load_struggle_notebook']).load_struggle_notebook(),
        "push_config": {k: v for k, v in load_push_config().items() if k != "smtp_pass"},
        "trend_stats": _compute_trends(checkin_data),
        "available_lists": {
            k: {"name": v["name"], "name_en": v["name_en"], "count": len(v["problems"])}
            for k, v in __import__('leetcode_auto.problem_lists', fromlist=['PROBLEM_LISTS']).PROBLEM_LISTS.items()
        },
        "problem_data": get_all_problem_data(),
        "optimizations": optimizations,
        "session_valid": check_session_cached(),
    }


def get_dashboard_data() -> dict:
    """Reload all data from files and return the full dashboard JSON."""
    from ..progress import (
        parse_progress_table, _compute_stats, _compute_streak,
        _get_review_due, _estimate_completion, _load_optimizations,
    )
    from ..features import parse_checkin_data
    from ..config import PROGRESS_FILE, CHECKIN_FILE

    _, rows = parse_progress_table(PROGRESS_FILE)
    stats = _compute_stats(rows)
    checkin_data = parse_checkin_data(CHECKIN_FILE)
    streak, total_days = _compute_streak(CHECKIN_FILE)
    review_due = _get_review_due(rows, date.today())
    est = _estimate_completion(stats, total_days)
    optimizations = _load_optimizations()
    return _build_comprehensive_data(
        rows, stats, checkin_data, streak,
        total_days, review_due, optimizations, est,
    )
