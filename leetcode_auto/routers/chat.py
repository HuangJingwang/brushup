"""Chat router: GET /api/chat/history, POST /api/chat."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    action: str = "send"
    message: str = ""
    history: list[dict[str, Any]] = []


@router.get("/chat/history")
def get_chat_history():
    from ..ai_analyzer import load_chat_history
    return {"history": load_chat_history()}


@router.post("/chat")
def post_chat(req: ChatRequest):
    if req.action == "clear":
        from ..ai_analyzer import clear_chat_history
        clear_chat_history()
        return {"ok": True}

    # Default: send message
    from ..config import get_ai_config
    ai_config = get_ai_config()
    if not ai_config["enabled"]:
        return {"error": "AI 未配置，请在 ~/.leetcode_auto/.env 中设置 AI_PROVIDER 和 AI_API_KEY"}

    from ..ai_analyzer import (
        build_chat_context, chat as ai_chat,
        save_chat_history, get_last_ai_error,
    )
    system_prompt = build_chat_context()
    history = req.history
    reply = ai_chat(req.message, history, system_prompt)
    if reply:
        history.append({"role": "user", "content": req.message})
        history.append({"role": "assistant", "content": reply})
        save_chat_history(history)
        return {"reply": reply}
    else:
        return {"error": get_last_ai_error() or "AI 请求失败，请重试"}
