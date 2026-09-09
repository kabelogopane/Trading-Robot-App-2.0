"""Performance statistics for paper-backtest results."""

from __future__ import annotations

from math import inf
from typing import Any, Iterable


def _r(trade: Any) -> float | None:
    value = trade["r_multiple"] if isinstance(trade, dict) else getattr(trade, "r_multiple")
    return None if value is None else float(value)


def calculate_performance(trades: Iterable[Any]) -> dict[str, float | int | None]:
    values = [_r(t) for t in trades]
    closed = [r for r in values if r is not None]
    wins = [r for r in closed if r > 0]
    losses = [r for r in closed if r < 0]

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for r in closed:
        equity += r
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    return {
        "trades": len(values),
        "closed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": (len(wins) / len(closed) * 100.0) if closed else None,
        "net_r": sum(closed) if closed else 0.0,
        "average_r": (sum(closed) / len(closed)) if closed else None,
        "max_drawdown_r": max_drawdown,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else (inf if gross_profit > 0 else None),
    }
