"""Session caching and validation service."""

from __future__ import annotations

import time
import threading
from typing import Optional

_SESSION_CACHE_LOCK = threading.Lock()
_SESSION_VALID: Optional[bool] = None  # None = not checked yet
_SESSION_CACHE_TIME: float = 0
_SESSION_CACHE_TTL = 120  # seconds


def check_session_cached() -> bool:
    """Return whether the current LeetCode session is valid, with caching."""
    global _SESSION_VALID, _SESSION_CACHE_TIME
    with _SESSION_CACHE_LOCK:
        now = time.time()
        if _SESSION_VALID is not None and (now - _SESSION_CACHE_TIME) < _SESSION_CACHE_TTL:
            return _SESSION_VALID
    # Do the actual check outside the lock
    from ..leetcode_api import load_credentials, check_session
    creds = load_credentials()
    if not creds.get("session"):
        valid = False
    else:
        result = check_session(creds["session"], creds["csrf"])
        # network_error -> assume valid (don't lock user out for transient issues)
        valid = bool(result.username) or result.network_error
    with _SESSION_CACHE_LOCK:
        _SESSION_VALID = valid
        _SESSION_CACHE_TIME = time.time()
    return valid


def invalidate_cache():
    """Force re-check on next call."""
    global _SESSION_VALID
    with _SESSION_CACHE_LOCK:
        _SESSION_VALID = None
