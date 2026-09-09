"""Tests for session grouping and 45-minute window assignment."""

from datetime import date

from backtest.session import assign_windows, group_by_session


def bar(ts, o=100, h=101, l=99, c=100.5):
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}


def test_group_by_session_uses_new_york_date():
    bars = [
        bar("2026-08-03T23:30:00+00:00"),
        bar("2026-08-04T00:30:00+00:00"),
    ]
    grouped = group_by_session(bars)
    assert list(grouped) == [date(2026, 8, 3), date(2026, 8, 4)]


def test_assign_windows_uses_start_inclusive_end_exclusive_rule():
    bars = [
        bar("2026-08-03T13:45:00+00:00"),  # 09:45 New York
        bar("2026-08-03T14:30:00+00:00"),  # 10:30 New York
        bar("2026-08-03T15:15:00+00:00"),  # 11:15 New York
    ]
    assigned = assign_windows(bars, date(2026, 8, 3))
    counts = [len(values) for values in assigned.values()]
    assert counts[0] == 1
    assert counts[1] == 1
    assert counts[2] == 1
