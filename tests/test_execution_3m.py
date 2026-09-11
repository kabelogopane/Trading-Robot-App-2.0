"""Tests for the 3-minute execution layer using US500 paper data."""

from data.loader import dataframe_to_bars, load_csv
from strategy.execution import find_3m_confirmation


def test_3m_sample_has_expected_frequency_and_anchor(tmp_path):
    frame = load_csv("data/sample_3m_us500.csv")
    bars = dataframe_to_bars(frame)
    assert len(bars) > 20
    assert bars[20]["timestamp"].hour == 13
    assert bars[20]["timestamp"].minute == 45


def test_execution_layer_never_confirms_without_anchor():
    bars = [
        {"timestamp": "2026-09-02T13:42:00Z", "open": 7698, "high": 7700, "low": 7695, "close": 7699}
    ]
    result = find_3m_confirmation(bars, reference_high=7701, reference_low=7690)
    assert result.qualified is False
    assert "09:45" in result.reason
