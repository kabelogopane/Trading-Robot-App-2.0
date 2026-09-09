"""Tests for New York time handling and 45-minute window boundaries."""

from datetime import date, datetime

from strategy.time_windows import (
    build_45m_windows,
    ensure_new_york,
    is_observation_time,
    window_for_timestamp,
)


def test_builds_eight_primary_windows():
    windows = build_45m_windows(date(2026, 8, 3))
    assert len(windows) == 8
    assert windows[0].start.strftime("%H:%M") == "09:45"
    assert windows[-1].end.strftime("%H:%M") == "15:45"


def test_boundary_belongs_to_next_window():
    windows = build_45m_windows(date(2026, 8, 3))
    boundary = datetime.fromisoformat("2026-08-03T10:30:00-04:00")
    assert window_for_timestamp(boundary) == windows[1]
    assert not windows[0].contains(boundary)


def test_before_anchor_is_not_in_primary_windows():
    before = datetime.fromisoformat("2026-08-03T09:44:59-04:00")
    assert window_for_timestamp(before) is None


def test_anchor_is_first_window():
    anchor = datetime.fromisoformat("2026-08-03T09:45:00-04:00")
    windows = build_45m_windows(date(2026, 8, 3))
    assert window_for_timestamp(anchor) == windows[0]


def test_observation_time_uses_new_york_clock():
    anchor = datetime.fromisoformat("2026-08-03T13:45:00+00:00")
    assert is_observation_time(anchor)


def test_naive_datetime_is_treated_as_new_york():
    value = datetime(2026, 8, 3, 9, 45)
    converted = ensure_new_york(value)
    assert converted.tzinfo is not None
    assert converted.strftime("%H:%M") == "09:45"
