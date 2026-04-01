"""Auth router: POST /api/login, POST /api/logout."""

from __future__ import annotations

import threading

from fastapi import APIRouter

from ..services.session_service import invalidate_cache

router = APIRouter(prefix="/api", tags=["auth"])

_LOGIN_LOCK = threading.Lock()
_LOGIN_RUNNING = False


@router.post("/login")
def login():
    global _LOGIN_RUNNING
    from ..leetcode_api import browser_login

    with _LOGIN_LOCK:
        if _LOGIN_RUNNING:
            return {"status": "running"}
        _LOGIN_RUNNING = True

    def _do_login():
        global _LOGIN_RUNNING
        try:
            browser_login()
            invalidate_cache()
            from ..sync import sync
            sync(interactive=False)
        except Exception as e:
            print(f"Login failed: {e}")
        finally:
            with _LOGIN_LOCK:
                _LOGIN_RUNNING = False

    threading.Thread(target=_do_login, daemon=True).start()
    return {"status": "started"}


@router.post("/logout")
def logout():
    from ..config import COOKIES_FILE, DATA_DIR

    if COOKIES_FILE.exists():
        COOKIES_FILE.unlink()
    pf = DATA_DIR / "user_profile.json"
    if pf.exists():
        pf.unlink()
    invalidate_cache()
    return {"ok": True}
