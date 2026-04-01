"""Focus router: POST /api/today-focus."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["focus"])


class FocusAction(BaseModel):
    action: str
    slug: str = ""


@router.post("/today-focus")
def today_focus(req: FocusAction):
    if req.action != "check_done":
        return {"error": "unknown"}
    try:
        from ..sync import sync
        sync(interactive=False)
        from ..web import _reload_data
        fresh = _reload_data()
        today_str = date.today().isoformat()
        row = next((r for r in fresh.get("rows", []) if r.get("slug") == req.slug), None)
        completed_today = bool(row and (row.get("r1") or "").strip() == today_str)
        result: dict = {
            "ok": True,
            "completed_today": completed_today,
            "today_focus": fresh.get("today_focus", []),
        }
        if not completed_today:
            result["message"] = "今天还没检测到这道题的新一轮完成记录。"
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
