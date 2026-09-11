"""Liquidity measurements used as supporting evidence only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LiquidityLevels:
    prior_high: float | None
    prior_low: float | None
    equal_high: float | None
    equal_low: float | None


def detect_liquidity(bars: Sequence[dict], tolerance: float = 0.0) -> LiquidityLevels:
    """Find prior and equal high/low references from already-known bars."""
    if not bars:
        return LiquidityLevels(None, None, None, None)
    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    equal_high = next((v for i, v in enumerate(highs) if any(i != j and abs(v - x) <= tolerance for j, x in enumerate(highs))), None)
    equal_low = next((v for i, v in enumerate(lows) if any(i != j and abs(v - x) <= tolerance for j, x in enumerate(lows))), None)
    return LiquidityLevels(max(highs), min(lows), equal_high, equal_low)


def swept_high(bar: dict, level: float) -> bool:
    """True when the bar trades above a reference high."""
    return float(bar["high"]) > float(level)


def swept_low(bar: dict, level: float) -> bool:
    """True when the bar trades below a reference low."""
    return float(bar["low"]) < float(level)


def sweep_and_reject_high(bar: dict, level: float) -> bool:
    """Measure a buy-side sweep that closes back at/below the level."""
    return swept_high(bar, level) and float(bar["close"]) <= float(level)


def sweep_and_reject_low(bar: dict, level: float) -> bool:
    """Measure a sell-side sweep that closes back at/above the level."""
    return swept_low(bar, level) and float(bar["close"]) >= float(level)
