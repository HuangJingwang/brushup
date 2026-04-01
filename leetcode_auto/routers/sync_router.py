"""Sync router: POST /api/sync."""

from __future__ import annotations

import threading

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync")
def start_sync():
    def _do_sync():
        try:
            from ..sync import sync
            sync(interactive=False)
        except Exception as e:
            print(f"Sync failed: {e}")

    threading.Thread(target=_do_sync, daemon=True).start()
    return {"status": "started"}
