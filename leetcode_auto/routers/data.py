"""Data router: GET /api/data."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.stats_service import get_dashboard_data

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/data")
def get_data():
    return get_dashboard_data()
