"""Helpers for grouping OHLC bars into New York trading sessions."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable

from strategy.time_windows import build_45m_windows, ensure_new_york, window_for_timestamp


def session_date(value: datetime) -> date:
    return ensure_new_york(value).date()


def group_by_session(bars: Iterable[Any]) -> dict[date, list[Any]]:
    grouped: dict[date, list[Any]] = defaultdict(list)
    for bar in bars:
        value = bar["timestamp"] if isinstance(bar, dict) else getattr(bar, "timestamp")
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        grouped[session_date(value)].append(bar)
    return {key: sorted(value, key=_bar_timestamp) for key, value in sorted(grouped.items())}


def _bar_timestamp(bar: Any) -> datetime:
    value = bar["timestamp"] if isinstance(bar, dict) else getattr(bar, "timestamp")
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)


def assign_windows(bars: Iterable[Any], day: date) -> dict[str, list[Any]]:
    """Assign bars to the eight 45-minute windows for a given New York date."""
    windows = build_45m_windows(day)
    result = {str(window): [] for window in windows}
    for bar in bars:
        window = window_for_timestamp(_bar_timestamp(bar))
        if window is not None and str(window) in result:
            result[str(window)].append(bar)
    return result
