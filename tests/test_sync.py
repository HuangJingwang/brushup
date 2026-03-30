"""Tests for sync.py: checkin rendering, progress collection, history backfill, dashboard."""

import json
import re
from datetime import datetime, date

import pytest


@pytest.fixture(autouse=True)
def _patch_config(monkeypatch, tmp_path):
    monkeypatch.setattr("leetcode_auto.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("leetcode_auto.config.PLAN_DIR", tmp_path)
    monkeypatch.setattr("leetcode_auto.config.PROGRESS_FILE", tmp_path / "progress.md")
    monkeypatch.setattr("leetcode_auto.config.CHECKIN_FILE", tmp_path / "checkin.md")
    monkeypatch.setattr("leetcode_auto.config.DASHBOARD_FILE", tmp_path / "dashboard.md")
    monkeypatch.setattr("leetcode_auto.config.PLAN_CONFIG_FILE", tmp_path / "plan_config.json")


SAMPLE_TABLE = """\
# 刷题进度表

| 序号 | 题目 | 难度 | R1 | R2 | R3 | R4 | R5 | 状态 | 最后完成日期 |
| ---: | --- | --- | :---: | :---: | :---: | :---: | :---: | --- | --- |
| 1 | [1. 两数之和](https://leetcode.cn/problems/two-sum/) | 简单 |   |   |   |   |   |   | — |
| 2 | [2. 两数相加](https://leetcode.cn/problems/add-two-numbers/) | 中等 | 2025-03-20 |   |   |   |   | 进行中 | 2025-03-20 |
| 3 | [3. 无重复字符](https://leetcode.cn/problems/longest-substring-without-repeating-characters/) | 中等 | 2025-03-18 | 2025-03-19 | 2025-03-22 | 2025-03-29 | 2025-04-12 | 已完成 | 2025-04-12 |
"""


def _write_table(path, content=SAMPLE_TABLE):
    path.write_text(content, encoding="utf-8")


def _parse_rows(tmp_path):
    f = tmp_path / "progress.md"
    _write_table(f)
    from leetcode_auto.progress import parse_progress_table
    _, rows = parse_progress_table(f)
    return rows


class TestRenderCheckinEntry:
    def test_basic_entry(self):
        from leetcode_auto.sync import _render_checkin_entry

        entry = _render_checkin_entry(
            "2025-03-25", 5, ["两数之和"], ["两数相加"], [],
        )
        assert "2025-03-25" in entry
        assert "Day 5" in entry
        assert "两数之和" in entry
        assert "两数相加" in entry
        assert "1 题" in entry  # new count
        assert "1 题" in entry  # review count
        assert "今日总题数：2" in entry

    def test_empty_lists(self):
        from leetcode_auto.sync import _render_checkin_entry

        entry = _render_checkin_entry("2025-03-25", 1, [], [], [])
        assert "新题完成：无（0 题）" in entry
        assert "复习完成：无（0 题）" in entry
        assert "今日总题数：0" in entry
        assert "卡点题目：无" in entry

    def test_struggles_listed(self):
        from leetcode_auto.sync import _render_checkin_entry

        entry = _render_checkin_entry(
            "2025-03-25", 1, [], [], ["两数之和"],
        )
        assert "卡点题目：两数之和" in entry

    def test_entry_ends_with_separator(self):
        from leetcode_auto.sync import _render_checkin_entry

        entry = _render_checkin_entry("2025-03-25", 1, [], [], [])
        assert entry.rstrip().endswith("---")


class TestCollectTodayProgress:
    def test_separates_new_and_review(self, tmp_path):
        from leetcode_auto.sync import _collect_today_progress

        rows = _parse_rows(tmp_path)
        # row[1] has r1=2025-03-20, so that's "new" on 2025-03-20
        new, review = _collect_today_progress(rows, "2025-03-20")
        new_flat = " ".join(new)
        assert "两数相加" in new_flat
        assert len(review) == 0

    def test_review_detected(self, tmp_path):
        from leetcode_auto.sync import _collect_today_progress

        rows = _parse_rows(tmp_path)
        # row[2] has r2=2025-03-19, which is a review
        new, review = _collect_today_progress(rows, "2025-03-19")
        review_flat = " ".join(review)
        assert "无重复字符" in review_flat

    def test_no_matches(self, tmp_path):
        from leetcode_auto.sync import _collect_today_progress

        rows = _parse_rows(tmp_path)
        new, review = _collect_today_progress(rows, "2099-01-01")
        assert new == []
        assert review == []


class TestBackfillHistoryProgress:
    def test_marks_history_rows(self, tmp_path):
        from leetcode_auto.sync import _backfill_history_progress

        rows = _parse_rows(tmp_path)
        # two-sum has no rounds done, should be backfilled
        imported = _backfill_history_progress(rows, {"two-sum"})
        assert len(imported) == 1
        assert rows[0]["r1"] == "历史"
        assert rows[0]["status"] == "进行中"

    def test_skips_already_started(self, tmp_path):
        from leetcode_auto.sync import _backfill_history_progress

        rows = _parse_rows(tmp_path)
        # add-two-numbers already has r1 filled
        imported = _backfill_history_progress(rows, {"add-two-numbers"})
        assert len(imported) == 0

    def test_skips_unknown_slugs(self, tmp_path):
        from leetcode_auto.sync import _backfill_history_progress

        rows = _parse_rows(tmp_path)
        imported = _backfill_history_progress(rows, {"nonexistent-problem"})
        assert len(imported) == 0


class TestNeedsHistoryBackfill:
    def test_needs_backfill_no_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "leetcode_auto.sync._HISTORY_SYNC_FILE",
            tmp_path / "history_sync.json",
        )
        from leetcode_auto.sync import _needs_history_backfill

        assert _needs_history_backfill("testuser") is True

    def test_no_backfill_when_matches(self, tmp_path, monkeypatch):
        state_file = tmp_path / "history_sync.json"
        monkeypatch.setattr(
            "leetcode_auto.sync._HISTORY_SYNC_FILE", state_file,
        )
        state = {"username": "testuser", "problem_list": "hot100"}
        state_file.write_text(json.dumps(state), encoding="utf-8")
        from leetcode_auto.sync import _needs_history_backfill

        assert _needs_history_backfill("testuser") is False

    def test_backfill_on_username_change(self, tmp_path, monkeypatch):
        state_file = tmp_path / "history_sync.json"
        monkeypatch.setattr(
            "leetcode_auto.sync._HISTORY_SYNC_FILE", state_file,
        )
        state = {"username": "olduser", "problem_list": "hot100"}
        state_file.write_text(json.dumps(state), encoding="utf-8")
        from leetcode_auto.sync import _needs_history_backfill

        assert _needs_history_backfill("newuser") is True


class TestUpdateCheckin:
    def _make_checkin(self, tmp_path, content):
        f = tmp_path / "checkin.md"
        f.write_text(content, encoding="utf-8")
        return f

    def test_creates_new_entry(self, tmp_path):
        from leetcode_auto.sync import update_checkin

        f = self._make_checkin(tmp_path, "# 每日打卡\n\n")
        update_checkin(f, "2025-03-25", ["两数之和"], ["两数相加"], [])
        content = f.read_text(encoding="utf-8")
        assert "2025-03-25" in content
        assert "Day 1" in content
        assert "两数之和" in content

    def test_updates_existing_entry(self, tmp_path):
        from leetcode_auto.sync import update_checkin

        f = self._make_checkin(tmp_path, "# 每日打卡\n\n")
        # First call creates the entry
        update_checkin(f, "2025-03-25", ["两数之和"], [], [])
        # Second call updates it
        update_checkin(f, "2025-03-25", ["两数之和", "两数相加"], ["无重复字符"], [])
        content = f.read_text(encoding="utf-8")
        # Should still have only one Day 1 section
        assert content.count("Day 1") == 1
        assert "两数相加" in content
        assert "无重复字符" in content

    def test_increments_day_number(self, tmp_path):
        from leetcode_auto.sync import update_checkin

        f = self._make_checkin(tmp_path, "# 每日打卡\n\n")
        update_checkin(f, "2025-03-24", ["两数之和"], [], [])
        update_checkin(f, "2025-03-25", ["两数相加"], [], [])
        content = f.read_text(encoding="utf-8")
        assert "Day 1" in content
        assert "Day 2" in content


class TestUpdateDashboard:
    def test_produces_valid_dashboard(self, tmp_path):
        from leetcode_auto.sync import update_dashboard
        from leetcode_auto.progress import parse_progress_table, _get_review_due

        f = tmp_path / "progress.md"
        _write_table(f)
        _, rows = parse_progress_table(f)

        dashboard = tmp_path / "dashboard.md"
        review_due = _get_review_due(rows, date(2025, 3, 21))
        update_dashboard(dashboard, rows, 2, review_due)

        content = dashboard.read_text(encoding="utf-8")
        assert "# Hot100 进度看板" in content
        assert "题目总数：3" in content
        assert "今日完成轮次：2" in content
        assert "完成率" in content

    def test_dashboard_with_no_review(self, tmp_path):
        from leetcode_auto.sync import update_dashboard
        from leetcode_auto.progress import parse_progress_table

        f = tmp_path / "progress.md"
        _write_table(f)
        _, rows = parse_progress_table(f)

        dashboard = tmp_path / "dashboard.md"
        update_dashboard(dashboard, rows, 0, [])

        content = dashboard.read_text(encoding="utf-8")
        assert "无到期复习题目" in content

    def test_dashboard_with_review_items(self, tmp_path):
        from leetcode_auto.sync import update_dashboard
        from leetcode_auto.progress import parse_progress_table

        f = tmp_path / "progress.md"
        _write_table(f)
        _, rows = parse_progress_table(f)

        review_due = [
            {"round": "R2", "title": "两数相加", "overdue": 0},
        ]
        dashboard = tmp_path / "dashboard.md"
        update_dashboard(dashboard, rows, 1, review_due)

        content = dashboard.read_text(encoding="utf-8")
        assert "两数相加" in content
        assert "今日到期" in content
