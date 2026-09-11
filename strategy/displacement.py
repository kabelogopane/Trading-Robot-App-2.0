"""Objective displacement measurements for the lower-timeframe confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Sequence


@dataclass(frozen=True)
class DisplacementResult:
    direction: str
    body_size: float
    range_size: float
    relative_strength: float
    body_ratio: float
    close_location: float
    confirmed: bool


def measure_displacement(
    bar: dict,
    history: Sequence[dict],
    multiplier: float = 1.5,
    min_body_ratio: float = 0.6,
    min_close_location: float = 0.7,
) -> DisplacementResult:
    """Confirm an unusually strong directional bar without future data."""
    high = float(bar["high"])
    low = float(bar["low"])
    open_ = float(bar["open"])
    close = float(bar["close"])
    range_size = max(high - low, 0.0)
    body_size = abs(close - open_)

    ranges = [max(float(b["high"]) - float(b["low"]), 0.0) for b in history]
    baseline = median(ranges) if ranges else 0.0
    relative = range_size / baseline if baseline > 0 else 0.0
    body_ratio = body_size / range_size if range_size > 0 else 0.0
    close_location = ((close - low) / range_size) if range_size > 0 else 0.5

    if close > open_:
        direction = "bullish"
        close_ok = close_location >= min_close_location
    elif close < open_:
        direction = "bearish"
        close_ok = close_location <= (1.0 - min_close_location)
    else:
        direction = "neutral"
        close_ok = False

    confirmed = (
        direction != "neutral"
        and relative >= multiplier
        and body_ratio >= min_body_ratio
        and close_ok
    )
    return DisplacementResult(
        direction, body_size, range_size, relative, body_ratio, close_location, confirmed
    )
