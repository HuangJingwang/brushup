"""Tests for storage.py: JSON / text file read-write helpers."""

import json
import os
import stat

import pytest

from leetcode_auto.storage import load_json, save_json, load_text, save_text


class TestLoadJson:
    def test_missing_file_returns_default(self, tmp_path):
        result = load_json(tmp_path / "missing.json", default={"a": 1})
        assert result == {"a": 1}

    def test_missing_file_returns_none_by_default(self, tmp_path):
        result = load_json(tmp_path / "missing.json")
        assert result is None

    def test_valid_json_returns_data(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value", "num": 42}', encoding="utf-8")
        result = load_json(f)
        assert result == {"key": "value", "num": 42}

    def test_corrupt_json_returns_default(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{not valid json!!!", encoding="utf-8")
        result = load_json(f, default={"fallback": True})
        assert result == {"fallback": True}

    def test_callable_default_is_called(self, tmp_path):
        result = load_json(tmp_path / "missing.json", default=dict)
        assert result == {}

    def test_callable_default_on_corrupt(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{broken", encoding="utf-8")
        result = load_json(f, default=list)
        assert result == []


class TestSaveJson:
    def test_creates_file_with_correct_content(self, tmp_path):
        f = tmp_path / "out.json"
        data = {"hello": "world", "nums": [1, 2, 3]}
        save_json(f, data)
        assert f.exists()
        loaded = json.loads(f.read_text(encoding="utf-8"))
        assert loaded == data

    def test_creates_parent_directories(self, tmp_path):
        f = tmp_path / "a" / "b" / "c" / "deep.json"
        save_json(f, {"deep": True})
        assert f.exists()
        assert json.loads(f.read_text(encoding="utf-8")) == {"deep": True}

    @pytest.mark.skipif(os.name == "nt", reason="Permission test not applicable on Windows")
    def test_secure_sets_restrictive_permissions(self, tmp_path):
        f = tmp_path / "secret.json"
        save_json(f, {"token": "abc"}, secure=True)
        mode = f.stat().st_mode
        assert mode & stat.S_IRUSR  # owner read
        assert mode & stat.S_IWUSR  # owner write
        assert not (mode & stat.S_IRGRP)  # no group read
        assert not (mode & stat.S_IROTH)  # no other read

    def test_non_ascii_content(self, tmp_path):
        f = tmp_path / "cjk.json"
        save_json(f, {"name": "两数之和"})
        raw = f.read_text(encoding="utf-8")
        assert "两数之和" in raw  # ensure_ascii=False


class TestLoadText:
    def test_missing_file_returns_default(self, tmp_path):
        result = load_text(tmp_path / "missing.txt")
        assert result == ""

    def test_missing_file_returns_custom_default(self, tmp_path):
        result = load_text(tmp_path / "missing.txt", default="N/A")
        assert result == "N/A"

    def test_existing_file_returns_content(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("Hello, World!", encoding="utf-8")
        assert load_text(f) == "Hello, World!"


class TestSaveText:
    def test_creates_file_with_correct_content(self, tmp_path):
        f = tmp_path / "out.txt"
        save_text(f, "line1\nline2\n")
        assert f.read_text(encoding="utf-8") == "line1\nline2\n"

    def test_creates_parent_directories(self, tmp_path):
        f = tmp_path / "sub" / "dir" / "file.txt"
        save_text(f, "nested")
        assert f.read_text(encoding="utf-8") == "nested"
