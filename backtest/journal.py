"""Trade-journal helpers for paper backtests."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

FIELDS = [
    "session_date", "window", "direction", "entry_time", "entry",
    "stop", "target", "exit_time", "exit_price", "outcome",
    "r_multiple", "reason",
]


def trade_rows(trades: Iterable[Any]) -> list[dict[str, Any]]:
    rows = []
    for trade in trades:
        row = trade.to_dict() if hasattr(trade, "to_dict") else dict(trade)
        rows.append({field: row.get(field) for field in FIELDS})
    return rows


def write_journal_csv(trades: Iterable[Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = trade_rows(trades)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output
