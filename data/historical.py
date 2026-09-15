"""Historical market-data preparation for the 45-minute research model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

import pandas as pd

from strategy.time_windows import ensure_new_york


@dataclass(frozen=True)
class HistoricalDataSummary:
    rows: int
    first_timestamp: str | None
    last_timestamp: str | None
    sessions: int
    timeframe_minutes: int | None


def load_historical_csv(path: str | Path) -> pd.DataFrame:
    """Load validated OHLC data and add New York session fields."""
    from data.loader import load_csv

    frame = load_csv(path).copy()
    frame["new_york_timestamp"] = frame["timestamp"].map(ensure_new_york)
    frame["session_date"] = frame["new_york_timestamp"].dt.date
    frame["session_time"] = frame["new_york_timestamp"].dt.time
    return frame


def filter_model_hours(
    frame: pd.DataFrame,
    start: time = time(8, 45),
    end: time = time(15, 45),
) -> pd.DataFrame:
    """Keep the model's New York observation period using [start, end)."""
    if start >= end:
        raise ValueError("start must be earlier than end")
    mask = (frame["session_time"] >= start) & (frame["session_time"] < end)
    return frame.loc[mask].copy().reset_index(drop=True)


def infer_timeframe_minutes(frame: pd.DataFrame) -> int | None:
    """Infer the most common candle interval in minutes."""
    if len(frame) < 2:
        return None
    deltas = frame["new_york_timestamp"].sort_values().diff().dropna()
    if deltas.empty:
        return None
    minutes = (deltas.dt.total_seconds() / 60).round().astype(int)
    mode = minutes.mode()
    return int(mode.iloc[0]) if not mode.empty else None


def summarize_historical_data(frame: pd.DataFrame) -> HistoricalDataSummary:
    """Return a compact summary for the dashboard and research reports."""
    if frame.empty:
        return HistoricalDataSummary(0, None, None, 0, None)
    return HistoricalDataSummary(
        rows=len(frame),
        first_timestamp=frame["new_york_timestamp"].iloc[0].isoformat(),
        last_timestamp=frame["new_york_timestamp"].iloc[-1].isoformat(),
        sessions=frame["session_date"].nunique(),
        timeframe_minutes=infer_timeframe_minutes(frame),
    )
