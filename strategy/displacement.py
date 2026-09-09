"""Objective displacement measurements."""

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
    confirmed: bool


def measure_displacement(
    bar: dict,
    history: Sequence[dict],
    multiplier: float = 1.5,
    min_body_ratio: float = 0.6,
) -> DisplacementResult:
    """Measure whether the current bar is unusually strong.

    Confirmation compares range to historical median range and requires a
    directional body occupying at least min_body_ratio of the bar range.
    """
    high = float(bar["high"])
    low = float(bar["low"])
    open_ = float(bar["open"])
    close = float(bar["close"])
    range_size = max(high - low, 0.0)
    body_size = abs(close - open_)

    historical_ranges = [
        max(float(b["high"]) - float(b["low"]), 0.0)
        for b in history
        if float(b["high"]) >= float(b["low"])
    ]
    baseline = median(historical_ranges) if historical_ranges else 0.0
    relative = (range_size / baseline) if baseline > 0 else 0.0
    body_ratio = (body_size / range_size) if range_size > 0 else 0.0

    if close > open_:
        direction = "bullish"
    elif close < open_:
        direction = "bearish"
    else:
        direction = "neutral"

    confirmed = direction != "neutral" and relative >= multiplier and body_ratio >= min_body_ratio
    return DisplacementResult(direction, body_size, range_size, relative, confirmed)
