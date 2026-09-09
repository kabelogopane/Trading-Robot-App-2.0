"""Liquidity-level measurements used as supporting evidence only."""

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
    """Find simple prior and equal high/low liquidity references."""
    if not bars:
        return LiquidityLevels(None, None, None, None)

    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    prior_high = max(highs)
    prior_low = min(lows)

    equal_high = None
    equal_low = None
    for i, value in enumerate(highs):
        if any(i != j and abs(value - other) <= tolerance for j, other in enumerate(highs)):
            equal_high = value
            break
    for i, value in enumerate(lows):
        if any(i != j and abs(value - other) <= tolerance for j, other in enumerate(lows)):
            equal_low = value
            break

    return LiquidityLevels(prior_high, prior_low, equal_high, equal_low)


def swept_high(bar: dict, level: float) -> bool:
    """True when a bar trades above a reference high."""
    return float(bar["high"]) > level


def swept_low(bar: dict, level: float) -> bool:
    """True when a bar trades below a reference low."""
    return float(bar["low"]) < level
