"""Tests for historical market-data preparation."""

from datetime import time

import pandas as pd

from data.historical import filter_model_hours, infer_timeframe_minutes, summarize_historical_data


def make_frame():
    timestamps = pd.to_datetime(
        [
            "2026-08-03T12:45:00Z",
            "2026-08-03T13:45:00Z",
            "2026-08-03T14:48:00Z",
            "2026-08-03T20:00:00Z",
        ],
        utc=True,
    )
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [100, 101, 102, 103],
            "high": [101, 102, 103, 104],
            "low": [99, 100, 101, 102],
            "close": [100.5, 101.5, 102.5, 103.5],
        }
    )
    from data.historical import load_historical_csv
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "history.csv"
        frame.to_csv(path, index=False)
        return load_historical_csv(path)


def test_model_hours_use_new_york_time_and_exclude_end_boundary():
    frame = make_frame()
    filtered = filter_model_hours(frame, start=time(8, 45), end=time(15, 45))
    assert len(filtered) == 3
    assert all(filtered["session_time"].map(lambda value: time(8, 45) <= value < time(15, 45)))


def test_infer_timeframe_uses_most_common_interval():
    frame = make_frame()
    assert infer_timeframe_minutes(frame) == 60


def test_summary_counts_sessions_and_rows():
    frame = make_frame()
    summary = summarize_historical_data(frame)
    assert summary.rows == 4
    assert summary.sessions == 1
    assert summary.timeframe_minutes == 60
