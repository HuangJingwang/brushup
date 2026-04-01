"""Resume router: GET/POST /api/resume, GET /api/resume/template, GET/POST /api/interview."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["resume"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ResumeRequest(BaseModel):
    action: str = ""
    content: str = ""
    message: str = ""
    history: list[dict[str, Any]] = []
    resume_id: str = ""
    name: str = ""
    file: str = ""


class InterviewRequest(BaseModel):
    action: str = ""
    content: str = ""
    message: str = ""
    history: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------

@router.get("/resume")
def get_resume():
    from ..resume import load_resume, load_analysis, load_resume_chat, get_resume_list
    return {
        "content": load_resume(),
        "analysis": load_analysis().get("text", ""),
        "chat_history": load_resume_chat(),
        "resume_list": get_resume_list(),
    }


@router.get("/resume/template")
def get_resume_template():
    from ..resume import RESUME_TEMPLATE
    return Response(
        content=RESUME_TEMPLATE.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=resume_template.md"},
    )


@router.get("/interview")
def get_interview():
    from ..resume import load_interview_questions, load_interview_chat, load_interview_report
    return {
        "questions": load_interview_questions(),
        "chat_history": load_interview_chat(),
        "report": load_interview_report(),
    }


# ---------------------------------------------------------------------------
# POST /api/resume
# ---------------------------------------------------------------------------

@router.post("/resume")
def post_resume(req: ResumeRequest):
    from ..resume import (
        save_resume, load_resume, analyze_resume,
        save_analysis, load_analysis,
        chat_resume, save_resume_chat, clear_resume_chat,
    )
    from ..ai_analyzer import get_last_ai_error
    action = req.action

    if action == "save":
        save_resume(req.content)
        return {"ok": True}

    elif action == "analyze":
        save_resume(req.content)
        analysis = analyze_resume(req.content)
        if analysis:
            save_analysis({"text": analysis})
            return {"analysis": analysis}
        else:
            return {"error": get_last_ai_error() or "AI not configured or request failed"}

    elif action == "chat":
        history = req.history
        resume_content = req.content or load_resume()
        if req.content:
            save_resume(req.content)
        analysis_text = load_analysis().get("text", "")
        reply = chat_resume(req.message, history, resume_content, analysis_text)
        if reply:
            history.append({"role": "user", "content": req.message})
            history.append({"role": "assistant", "content": reply})
            save_resume_chat(history)
            return {"reply": reply}
        else:
            return {"error": get_last_ai_error() or "AI not configured or request failed"}

    elif action == "clear_chat":
        clear_resume_chat()
        return {"ok": True}

    elif action == "switch_resume":
        from ..resume import switch_resume
        switch_resume(req.resume_id or "default")
        return {"ok": True}

    elif action == "create_resume":
        from ..resume import create_resume
        new_id = create_resume(req.name or "新简历")
        return {"ok": True, "id": new_id}

    elif action == "delete_resume":
        from ..resume import delete_resume
        delete_resume(req.resume_id)
        return {"ok": True}

    elif action == "rename_resume":
        from ..resume import rename_resume
        rename_resume(req.resume_id, req.name)
        return {"ok": True}

    elif action == "list_versions":
        from ..resume import get_resume_versions
        return {"versions": get_resume_versions()}

    elif action == "restore_version":
        from ..resume import restore_resume_version
        content = restore_resume_version(req.file)
        return {"ok": True, "content": content}

    else:
        return {"error": "unknown action"}


# ---------------------------------------------------------------------------
# POST /api/interview
# ---------------------------------------------------------------------------

@router.post("/interview")
def post_interview(req: InterviewRequest):
    from ..resume import (
        load_resume, generate_interview_questions,
        chat_interview, save_interview_chat, clear_interview_chat,
    )
    from ..ai_analyzer import get_last_ai_error
    action = req.action

    if action == "generate":
        from ..resume import save_resume as _sr
        _sr(req.content)
        questions = generate_interview_questions(req.content)
        if questions:
            return {"questions": questions}
        else:
            return {"error": get_last_ai_error() or "AI 未配置或请求失败"}

    elif action == "start":
        resume_content = load_resume()
        if not resume_content:
            return {"error": "请先粘贴简历内容"}
        reply = chat_interview("请开始面试", [], resume_content)
        if reply:
            save_interview_chat([{"role": "assistant", "content": reply}])
            return {"reply": reply}
        else:
            return {"error": get_last_ai_error() or "AI 未配置或请求失败"}

    elif action == "chat":
        history = req.history
        resume_content = load_resume()
        reply = chat_interview(req.message, history, resume_content)
        if reply:
            history.append({"role": "user", "content": req.message})
            history.append({"role": "assistant", "content": reply})
            save_interview_chat(history)
            return {"reply": reply}
        else:
            return {"error": get_last_ai_error() or "AI 未配置或请求失败"}

    elif action == "clear":
        clear_interview_chat()
        return {"ok": True}

    elif action == "report":
        from ..resume import generate_interview_report, load_interview_chat as _lic
        hist = _lic()
        report = generate_interview_report(hist)
        if report:
            return {"report": report}
        else:
            return {"error": "AI 未配置或对话为空"}

    else:
        return {"error": "未知操作"}
