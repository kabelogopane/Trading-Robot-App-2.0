"""Data-quality checks for historical US500 research datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

import pandas as pd


@dataclass(frozen=True)
class DataQualityReport:
    rows: int
    columns_ok: bool
    timezone_ok: bool
    chronological: bool
    duplicate_timestamps: int
    ohlc_valid: bool
    expected_timeframe_minutes: int | None
    detected_timeframe_minutes: int | None
    gaps: int
    sessions: int
    anchor_0945_sessions: int
    model_coverage_sessions: int
    passed: bool


def assess_quality(
    frame: pd.DataFrame,
    expected_timeframe_minutes: int = 3,
) -> DataQualityReport:
    """Check whether a historical dataset is suitable for the time model."""
    required = {"timestamp", "open", "high", "low", "close"}
    columns_ok = required.issubset(frame.columns)
    if not columns_ok:
        return DataQualityReport(len(frame), False, False, False, 0, False, expected_timeframe_minutes, None, 0, 0, 0, 0, False)

    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    timezone_ok = timestamps.notna().all()
    chronological = timestamps.is_monotonic_increasing
    duplicate_count = int(timestamps.duplicated().sum())

    numeric = frame[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    ohlc_valid = bool(numeric.notna().all().all())
    if ohlc_valid:
        ohlc_valid = bool(
            (numeric["high"] >= numeric[["open", "close"]].max(axis=1)).all()
            and (numeric["low"] <= numeric[["open", "close"]].min(axis=1)).all()
            and (numeric["high"] >= numeric["low"]).all()
        )

    detected = None
    gaps = 0
    sessions = 0
    anchors = 0
    coverage = 0
    if timezone_ok and len(timestamps) >= 2:
        ny = timestamps.dt.tz_convert("America/New_York")
        deltas = timestamps.diff().dropna().dt.total_seconds().div(60)
        if not deltas.empty:
            mode = deltas.round().mode()
            detected = int(mode.iloc[0]) if not mode.empty else None
            gaps = int((deltas > expected_timeframe_minutes).sum())
        session_dates = ny.dt.date
        sessions = int(session_dates.nunique())
        times = ny.dt.time
        grouped = pd.DataFrame({"date": session_dates, "time": times}).groupby("date")
        for _, group in grouped:
            values = set(group["time"])
            if time(9, 45) in values:
                anchors += 1
            if time(8, 45) in values and time(15, 44) in values:
                coverage += 1

    passed = bool(
        columns_ok
        and timezone_ok
        and chronological
        and duplicate_count == 0
        and ohlc_valid
        and detected == expected_timeframe_minutes
        and gaps == 0
        and anchors > 0
        and coverage > 0
    )
    return DataQualityReport(
        rows=len(frame), columns_ok=columns_ok, timezone_ok=timezone_ok,
        chronological=chronological, duplicate_timestamps=duplicate_count,
        ohlc_valid=ohlc_valid, expected_timeframe_minutes=expected_timeframe_minutes,
        detected_timeframe_minutes=detected, gaps=gaps, sessions=sessions,
        anchor_0945_sessions=anchors, model_coverage_sessions=coverage, passed=passed,
    )
