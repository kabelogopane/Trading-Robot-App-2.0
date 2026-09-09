"""Human-readable and JSON-friendly backtest reporting."""

from __future__ import annotations

import json
from typing import Any, Iterable

from backtest.performance import calculate_performance


def build_report(trades: Iterable[Any]) -> dict[str, Any]:
    trade_list = [t.to_dict() if hasattr(t, "to_dict") else dict(t) for t in trades]
    return {
        "summary": calculate_performance(trade_list),
        "trades": trade_list,
    }


def report_as_json(trades: Iterable[Any], indent: int = 2) -> str:
    return json.dumps(build_report(trades), indent=indent, default=str, allow_nan=False)


def report_as_text(trades: Iterable[Any]) -> str:
    report = build_report(trades)
    s = report["summary"]
    pf = s["profit_factor"]
    pf_text = "inf" if pf == float("inf") else ("n/a" if pf is None else f"{pf:.2f}")
    lines = [
        "Time-Based Trading Robot — Paper Backtest Report",
        "=" * 52,
        f"Trades: {s['trades']}",
        f"Closed trades: {s['closed_trades']}",
        f"Wins: {s['wins']}",
        f"Losses: {s['losses']}",
        f"Win rate: {s['win_rate_pct']:.2f}%" if s['win_rate_pct'] is not None else "Win rate: n/a",
        f"Net R: {s['net_r']:.2f}",
        f"Average R: {s['average_r']:.2f}" if s['average_r'] is not None else "Average R: n/a",
        f"Max drawdown: {s['max_drawdown_r']:.2f} R",
        f"Profit factor: {pf_text}",
        "",
        "Research/paper simulation only — no real-money trades are placed.",
    ]
    return "\n".join(lines)
