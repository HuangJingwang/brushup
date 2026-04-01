"""Problems router: POST /api/problem."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["problems"])


class ProblemAction(BaseModel):
    action: str
    slug: str = ""
    note: str = ""
    seconds: int = 0
    viewed: bool = False
    repeat: bool = False


@router.post("/problem")
def problem_action(req: ProblemAction):
    if req.action == "save_note":
        from ..problem_data import save_note
        save_note(req.slug, req.note)
    elif req.action == "add_time":
        from ..problem_data import add_time_spent
        add_time_spent(req.slug, req.seconds)
    elif req.action == "set_solution_viewed":
        from ..problem_data import set_solution_viewed
        set_solution_viewed(req.slug, req.viewed)
    elif req.action == "set_must_repeat":
        from ..problem_data import set_must_repeat
        set_must_repeat(req.slug, req.repeat)
    else:
        return {"error": "unknown"}
    return {"ok": True}
