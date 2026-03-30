"""Tests for daemon.py: schedule parsing and Schedule class."""

import pytest

from leetcode_auto.daemon import parse_schedule, Schedule


class TestParseScheduleInterval:
    def test_10m(self):
        s = parse_schedule("10m")
        assert s.mode == "interval"
        assert s.interval_seconds == 600

    def test_1h(self):
        s = parse_schedule("1h")
        assert s.mode == "interval"
        assert s.interval_seconds == 3600

    def test_2h(self):
        s = parse_schedule("2h")
        assert s.mode == "interval"
        assert s.interval_seconds == 7200

    def test_30m(self):
        s = parse_schedule("30m")
        assert s.mode == "interval"
        assert s.interval_seconds == 1800

    def test_whitespace_stripped(self):
        s = parse_schedule("  10m  ")
        assert s.interval_seconds == 600

    def test_case_insensitive(self):
        s = parse_schedule("2H")
        assert s.interval_seconds == 7200


class TestParseScheduleDaily:
    def test_2300(self):
        s = parse_schedule("23:00")
        assert s.mode == "daily"
        assert s.hour == 23
        assert s.minute == 0

    def test_0830(self):
        s = parse_schedule("08:30")
        assert s.mode == "daily"
        assert s.hour == 8
        assert s.minute == 30


class TestParseScheduleErrors:
    def test_invalid_string(self):
        with pytest.raises(ValueError):
            parse_schedule("invalid")

    def test_zero_minutes(self):
        with pytest.raises(ValueError):
            parse_schedule("0m")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_schedule("")


class TestScheduleHumanStr:
    def test_interval_hours(self):
        s = Schedule("interval", interval_seconds=7200, raw="2h")
        assert s.human_str() == "每 2 小时"

    def test_interval_minutes(self):
        s = Schedule("interval", interval_seconds=600, raw="10m")
        assert s.human_str() == "每 10 分钟"

    def test_daily(self):
        s = Schedule("daily", hour=23, minute=0, raw="23:00")
        assert s.human_str() == "每天 23:00"

    def test_daily_with_minutes(self):
        s = Schedule("daily", hour=8, minute=30, raw="08:30")
        assert s.human_str() == "每天 08:30"


class TestScheduleRoundtrip:
    def test_to_dict_and_from_dict(self):
        original = Schedule("interval", interval_seconds=600, hour=0, minute=0, raw="10m")
        d = original.to_dict()
        restored = Schedule.from_dict(d)
        assert restored.mode == original.mode
        assert restored.interval_seconds == original.interval_seconds
        assert restored.hour == original.hour
        assert restored.minute == original.minute
        assert restored.raw == original.raw

    def test_daily_roundtrip(self):
        original = Schedule("daily", hour=23, minute=0, raw="23:00")
        d = original.to_dict()
        restored = Schedule.from_dict(d)
        assert restored.mode == "daily"
        assert restored.hour == 23
        assert restored.minute == 0

    def test_to_dict_keys(self):
        s = Schedule("interval", interval_seconds=600, raw="10m")
        d = s.to_dict()
        assert set(d.keys()) == {"mode", "interval_seconds", "hour", "minute", "raw"}
