"""Historical OHLC data loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close"}


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load OHLC candles from CSV and normalize timestamps to UTC-aware values."""
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")

    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="first")
    frame = frame.reset_index(drop=True)

    if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
        raise ValueError("Invalid OHLC data: high is below open or close")
    if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
        raise ValueError("Invalid OHLC data: low is above open or close")
    if (frame["high"] < frame["low"]).any():
        raise ValueError("Invalid OHLC data: high is below low")

    return frame


def dataframe_to_bars(frame: pd.DataFrame) -> list[dict]:
    """Convert a validated DataFrame into the bar dictionaries used by the engine."""
    required = REQUIRED_COLUMNS
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    return [
        {
            "timestamp": row.timestamp.to_pydatetime(),
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
        }
        for row in frame.itertuples(index=False)
    ]
