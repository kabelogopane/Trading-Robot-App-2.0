"""Supporting market-structure measurements for the time-based model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class StructureResult:
    classification: str
    swing_high: float | None
    swing_low: float | None
    higher_high: bool = False
    higher_low: bool = False
    lower_high: bool = False
    lower_low: bool = False


def classify_structure(bars: Sequence[dict], lookback: int = 2) -> StructureResult:
    """Classify structure from simple confirmed swing points.

    This is deliberately a supporting measurement. It does not create a trade
    signal by itself. Bars require open/high/low/close keys.
    """
    if len(bars) < (lookback * 2 + 1):
        return StructureResult("neutral", None, None)

    highs: list[float] = []
    lows: list[float] = []
    for i in range(lookback, len(bars) - lookback):
        h = float(bars[i]["high"])
        l = float(bars[i]["low"])
        left = bars[i - lookback:i]
        right = bars[i + 1:i + lookback + 1]
        if all(h > float(b["high"]) for b in left + right):
            highs.append(h)
        if all(l < float(b["low"]) for b in left + right):
            lows.append(l)

    hh = len(highs) >= 2 and highs[-1] > highs[-2]
    lh = len(highs) >= 2 and highs[-1] < highs[-2]
    hl = len(lows) >= 2 and lows[-1] > lows[-2]
    ll = len(lows) >= 2 and lows[-1] < lows[-2]

    if hh and hl:
        classification = "bullish"
    elif lh and ll:
        classification = "bearish"
    else:
        classification = "neutral"

    return StructureResult(
        classification,
        highs[-1] if highs else None,
        lows[-1] if lows else None,
        hh, hl, lh, ll,
    )
