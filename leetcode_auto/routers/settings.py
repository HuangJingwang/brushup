"""Settings router: POST /api/settings, POST /api/push-config."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["settings"])


class SettingsRequest(BaseModel):
    problem_list: str = "hot100"
    rounds: int = 5
    intervals: list[int] = [1, 3, 7, 14, 30]
    daily_new: int = 3
    daily_review: int = 5
    deadline: str = ""


class PushConfigRequest(BaseModel):
    action: str = "save"
    config: dict[str, Any] = {}


@router.post("/settings")
def post_settings(req: SettingsRequest):
    from ..config import load_plan_config, save_plan_config
    old_cfg = load_plan_config()
    new_list = req.problem_list
    old_list = old_cfg.get("problem_list", "hot100")
    save_plan_config(req.model_dump())
    if new_list != old_list:
        import shutil
        from ..config import PROGRESS_FILE, PLAN_DIR
        from ..problem_lists import get_problem_list
        from ..init_plan import _gen_progress_table
        from ..storage import save_text
        backup = PLAN_DIR / f"01_进度表_{old_list}.md"
        if PROGRESS_FILE.exists() and not backup.exists():
            shutil.copy2(PROGRESS_FILE, backup)
        restore = PLAN_DIR / f"01_进度表_{new_list}.md"
        if restore.exists():
            shutil.copy2(restore, PROGRESS_FILE)
        else:
            problems = get_problem_list(new_list)
            save_text(PROGRESS_FILE, _gen_progress_table(problems))
    return {"ok": True}


@router.post("/push-config")
def post_push_config(req: PushConfigRequest):
    if req.action == "save":
        from ..config import save_push_config
        save_push_config(req.config)
        return {"ok": True}
    elif req.action == "test":
        from ..features import push_report
        push_report("BrushUp Test: If you see this, push is working!")
        return {"ok": True}
    else:
        return {"error": "unknown"}
