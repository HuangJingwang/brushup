"""统一数据存取层：JSON / 文本文件读写，统一编码、异常处理和权限管理。"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, Optional


def load_json(path: Path, default: Any = None) -> Any:
    """读取 JSON 文件，失败返回 default（默认 None）。"""
    if not path.exists():
        return default() if callable(default) else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default() if callable(default) else default


def save_json(path: Path, data: Any, *, indent: int = 2, secure: bool = False):
    """写入 JSON 文件。secure=True 时设置 600 权限。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )
    if secure:
        _set_owner_only(path)


def load_text(path: Path, default: str = "") -> str:
    """读取文本文件，失败返回 default。"""
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


def save_text(path: Path, content: str, *, secure: bool = False):
    """写入文本文件。secure=True 时设置 600 权限。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if secure:
        _set_owner_only(path)


def _set_owner_only(path: Path):
    """设置文件权限为仅所有者可读写（600）。Windows 上跳过。"""
    try:
        if os.name != "nt":
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
