"""Paper-simulation risk calculations.

This module calculates hypothetical position sizing only. It never sends orders.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    account_size: float = 10_000.0
    risk_percent: float = 1.0
    max_risk_percent: float = 2.0


@dataclass(frozen=True)
class PositionSize:
    risk_amount: float
    distance_to_stop: float
    units: float


def calculate_position_size(
    entry: float,
    stop: float,
    config: RiskConfig | None = None,
) -> PositionSize:
    """Calculate hypothetical units from account risk and stop distance."""
    cfg = config or RiskConfig()

    if cfg.account_size <= 0:
        raise ValueError("account_size must be greater than zero")
    if not 0 < cfg.risk_percent <= cfg.max_risk_percent:
        raise ValueError("risk_percent must be positive and within the configured maximum")

    distance = abs(float(entry) - float(stop))
    if distance <= 0:
        raise ValueError("entry and stop must be different")

    risk_amount = cfg.account_size * (cfg.risk_percent / 100.0)
    units = risk_amount / distance

    return PositionSize(
        risk_amount=risk_amount,
        distance_to_stop=distance,
        units=units,
    )
