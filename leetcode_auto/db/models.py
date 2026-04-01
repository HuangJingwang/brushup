"""Dataclass models for database rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Problem:
    slug: str
    title: str
    num: int
    difficulty: str
    category: str = ""
    notes: str = ""
    must_repeat: bool = False
    solution_viewed: bool = False


@dataclass
class ProgressEntry:
    slug: str
    round: str
    completed_date: str


@dataclass
class AiReview:
    id: int
    slug: str
    round: str
    date: str
    analysis: str


@dataclass
class CheckinEntry:
    date: str
    day_num: int
    new_count: int = 0
    review_count: int = 0
    total: int = 0
    new_problems: str = ""
    review_problems: str = ""
    struggles: str = ""


@dataclass
class TimeRecord:
    id: int
    slug: str
    seconds: int
    created_at: str = ""
