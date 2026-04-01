"""SQLite database connection and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import DATA_DIR

DB_PATH = DATA_DIR / "brushup.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS problems (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            num INTEGER,
            difficulty TEXT,
            category TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            must_repeat INTEGER DEFAULT 0,
            solution_viewed INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS progress (
            slug TEXT NOT NULL,
            round TEXT NOT NULL,
            completed_date TEXT NOT NULL,
            PRIMARY KEY (slug, round),
            FOREIGN KEY (slug) REFERENCES problems(slug)
        );
        CREATE TABLE IF NOT EXISTS checkins (
            date TEXT PRIMARY KEY,
            day_num INTEGER,
            new_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            new_problems TEXT DEFAULT '',
            review_problems TEXT DEFAULT '',
            struggles TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS ai_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            round TEXT NOT NULL,
            date TEXT NOT NULL,
            analysis TEXT NOT NULL,
            FOREIGN KEY (slug) REFERENCES problems(slug)
        );
        CREATE TABLE IF NOT EXISTS time_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            seconds INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (slug) REFERENCES problems(slug)
        );
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
