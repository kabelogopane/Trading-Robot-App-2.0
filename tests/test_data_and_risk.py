"""Tests for historical-data validation and hypothetical risk sizing."""

import pandas as pd
import pytest

from data.loader import dataframe_to_bars
from risk.risk_manager import RiskConfig, calculate_position_size


def test_dataframe_to_bars_normalizes_numeric_values():
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-08-03T13:45:00Z"], utc=True),
            "open": [100],
            "high": [105],
            "low": [99],
            "close": [104],
        }
    )
    bars = dataframe_to_bars(frame)
    assert len(bars) == 1
    assert bars[0]["open"] == 100.0
    assert bars[0]["close"] == 104.0


def test_dataframe_to_bars_rejects_missing_columns():
    frame = pd.DataFrame({"timestamp": ["2026-08-03T13:45:00Z"]})
    with pytest.raises(ValueError, match="Missing required columns"):
        dataframe_to_bars(frame)


def test_position_size_is_hypothetical():
    result = calculate_position_size(
        entry=100,
        stop=95,
        config=RiskConfig(account_size=10_000, risk_percent=1),
    )
    assert result.risk_amount == 100
    assert result.distance_to_stop == 5
    assert result.units == 20


def test_position_size_rejects_zero_stop_distance():
    with pytest.raises(ValueError, match="different"):
        calculate_position_size(entry=100, stop=100)


def test_position_size_rejects_risk_above_limit():
    with pytest.raises(ValueError, match="maximum"):
        calculate_position_size(
            entry=100,
            stop=95,
            config=RiskConfig(risk_percent=3, max_risk_percent=2),
        )
