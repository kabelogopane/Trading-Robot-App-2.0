"""Testable target and R-multiple calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeLevels:
    entry: float
    stop: float
    target: float
    risk_per_unit: float
    reward_per_unit: float
    rr: float


def calculate_levels(entry: float, stop: float, rr: float = 2.0) -> TradeLevels:
    """Calculate a fixed-R target from entry and invalidation."""
    if rr <= 0:
        raise ValueError("rr must be greater than zero")

    entry = float(entry)
    stop = float(stop)
    risk = abs(entry - stop)
    if risk == 0:
        raise ValueError("entry and stop cannot be equal")

    if stop < entry:
        target = entry + risk * rr
    else:
        target = entry - risk * rr

    return TradeLevels(
        entry=entry,
        stop=stop,
        target=target,
        risk_per_unit=risk,
        reward_per_unit=risk * rr,
        rr=float(rr),
    )


def r_multiple(direction: str, entry: float, exit_price: float, stop: float) -> float:
    """Return realized R for a hypothetical long or short trade."""
    risk = abs(float(entry) - float(stop))
    if risk == 0:
        raise ValueError("entry and stop cannot be equal")

    normalized = direction.lower()
    if normalized in {"long", "bullish"}:
        return (float(exit_price) - float(entry)) / risk
    if normalized in {"short", "bearish"}:
        return (float(entry) - float(exit_price)) / risk
    raise ValueError("direction must be 'long', 'short', 'bullish', or 'bearish'")
