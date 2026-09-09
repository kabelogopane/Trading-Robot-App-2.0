"""09:45 primary-anchor detection for the time-based model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time

from .time_windows import NEW_YORK, TimeWindow, build_45m_windows, ensure_new_york

ANCHOR_TIME = time(9, 45)


@dataclass(frozen=True)
class Anchor:
    """Represents the detected 09:45 New York-time anchor."""

    timestamp: datetime
    windows: tuple[TimeWindow, ...]

    @property
    def date(self) -> date:
        return self.timestamp.date()


def anchor_timestamp(date_value: date) -> datetime:
    """Return the 09:45 ET timestamp for a calendar date."""
    return datetime.combine(date_value, ANCHOR_TIME, tzinfo=NEW_YORK)


def is_anchor(timestamp: datetime) -> bool:
    """Return True when timestamp is exactly the 09:45 ET anchor."""
    ts = ensure_new_york(timestamp)
    return (
        ts.hour == ANCHOR_TIME.hour
        and ts.minute == ANCHOR_TIME.minute
        and ts.second == 0
        and ts.microsecond == 0
    )


def detect_anchor(timestamp: datetime) -> Anchor | None:
    """Detect a 09:45 anchor and construct that session's 45-minute windows.

    This function only detects time. It does not infer bullish or bearish
    direction and does not create a trade signal.
    """
    ts = ensure_new_york(timestamp)
    if not is_anchor(ts):
        return None

    windows = tuple(build_45m_windows(ts.date()))
    return Anchor(timestamp=ts, windows=windows)


def anchor_for_date(date_value: date) -> Anchor:
    """Build the research anchor for a known calendar date."""
    ts = anchor_timestamp(date_value)
    return Anchor(timestamp=ts, windows=tuple(build_45m_windows(date_value)))
