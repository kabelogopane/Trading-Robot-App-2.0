"""Deterministic New York-time window logic for the 45-minute model.

The time model is the primary framework. This module deliberately contains no
trade-direction logic and no ICT/SMC assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")

OBSERVATION_TIMES = (
    time(8, 45),
    time(9, 45),
    time(10, 45),
    time(11, 45),
    time(12, 45),
    time(13, 45),
    time(15, 45),
)

PRIMARY_WINDOW_START = time(9, 45)
PRIMARY_WINDOW_END = time(15, 45)
WINDOW_MINUTES = 45


@dataclass(frozen=True)
class TimeWindow:
    """A half-open [start, end) research window."""

    start: datetime
    end: datetime

    def contains(self, timestamp: datetime) -> bool:
        """Return True when timestamp belongs to this window.

        End timestamps are excluded, so a candle exactly on the boundary is
        assigned to the following window.
        """
        ts = ensure_new_york(timestamp)
        return self.start <= ts < self.end

    @property
    def label(self) -> str:
        return f"{self.start:%H:%M}→{self.end:%H:%M}"


def ensure_new_york(timestamp: datetime) -> datetime:
    """Normalize an aware timestamp to America/New_York.

    Naive datetimes are treated as New York time. This is intentional for
    historical CSV research where timestamps may be supplied without an
    offset.
    """
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=NEW_YORK)
    return timestamp.astimezone(NEW_YORK)


def _at(date_value, clock: time) -> datetime:
    return datetime.combine(date_value, clock, tzinfo=NEW_YORK)


def observation_datetimes(date_value) -> list[datetime]:
    """Return all configured observation times for a calendar date."""
    return [_at(date_value, clock) for clock in OBSERVATION_TIMES]


def build_45m_windows(date_value) -> list[TimeWindow]:
    """Build the eight consecutive windows from 09:45 through 15:45."""
    start = _at(date_value, PRIMARY_WINDOW_START)
    end = _at(date_value, PRIMARY_WINDOW_END)

    windows: list[TimeWindow] = []
    current = start
    delta = timedelta(minutes=WINDOW_MINUTES)

    while current < end:
        next_boundary = min(current + delta, end)
        windows.append(TimeWindow(start=current, end=next_boundary))
        current = next_boundary

    return windows


def window_for_timestamp(timestamp: datetime) -> TimeWindow | None:
    """Return the primary 45-minute window containing timestamp, if any."""
    ts = ensure_new_york(timestamp)
    for window in build_45m_windows(ts.date()):
        if window.contains(ts):
            return window
    return None


def is_observation_time(timestamp: datetime) -> bool:
    """Check whether a timestamp is exactly one of the model's observation times."""
    ts = ensure_new_york(timestamp)
    return ts.time().replace(second=0, microsecond=0) in OBSERVATION_TIMES
