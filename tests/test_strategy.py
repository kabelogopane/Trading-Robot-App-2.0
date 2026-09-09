"""Tests for the core 45-minute time-based strategy components."""

from datetime import date, datetime

import pytest

from strategy.displacement import measure_displacement
from strategy.entries import qualify_entry
from strategy.liquidity import detect_liquidity, swept_high, swept_low
from strategy.market_structure import classify_structure
from strategy.targets import calculate_levels, r_multiple


def bar(ts, o, h, l, c):
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}


def test_market_structure_bullish():
    bars = [
        bar("2026-08-03T10:00:00-04:00", 100, 103, 99, 102),
        bar("2026-08-03T10:03:00-04:00", 102, 104, 100, 103),
        bar("2026-08-03T10:06:00-04:00", 103, 105, 101, 104),
        bar("2026-08-03T10:09:00-04:00", 104, 106, 102, 105),
        bar("2026-08-03T10:12:00-04:00", 105, 107, 103, 106),
    ]
    result = classify_structure(bars, lookback=1)
    assert result.classification in {"bullish", "neutral"}


def test_liquidity_detects_prior_extremes_and_sweeps():
    bars = [
        bar("2026-08-03T10:00:00-04:00", 100, 105, 99, 103),
        bar("2026-08-03T10:03:00-04:00", 103, 104, 98, 101),
        bar("2026-08-03T10:06:00-04:00", 101, 106, 100, 105),
    ]
    levels = detect_liquidity(bars)
    assert levels.prior_high == 106
    assert levels.prior_low == 98
    assert swept_high({"high": 107}, levels.prior_high)
    assert swept_low({"low": 97}, levels.prior_low)


def test_displacement_requires_large_directional_bar():
    history = [
        bar(f"2026-08-03T10:{i:02d}:00-04:00", 100, 101, 99, 100.5)
        for i in range(0, 15, 3)
    ]
    current = bar("2026-08-03T10:15:00-04:00", 100, 105, 99.5, 104.5)
    result = measure_displacement(current, history, multiplier=1.2, min_body_ratio=0.6)
    assert result.confirmed
    assert result.direction == "bullish"


def test_entry_requires_all_confirmations():
    structure = type("S", (), {"classification": "bullish"})()
    displacement = type(
        "D", (), {"confirmed": True, "direction": "bullish"}
    )()
    signal = qualify_entry(
        direction="bullish",
        structure=structure,
        displacement=displacement,
        liquidity_swept=True,
        current_price=105,
        anchor_high=110,
        anchor_low=100,
    )
    assert signal.qualified
    assert signal.entry == 105
    assert signal.invalidation == 100


def test_entry_rejects_missing_liquidity_confirmation():
    structure = type("S", (), {"classification": "bullish"})()
    displacement = type(
        "D", (), {"confirmed": True, "direction": "bullish"}
    )()
    signal = qualify_entry(
        direction="bullish",
        structure=structure,
        displacement=displacement,
        liquidity_swept=False,
        current_price=105,
        anchor_high=110,
        anchor_low=100,
    )
    assert not signal.qualified


def test_target_calculation_and_r_multiple():
    levels = calculate_levels(entry=100, stop=95, rr=2)
    assert levels.target == 110
    assert levels.risk_per_unit == 5
    assert r_multiple("bullish", 100, 110, 95) == pytest.approx(2.0)
    assert r_multiple("bearish", 100, 90, 105) == pytest.approx(2.0)


def test_invalid_target_inputs_raise():
    with pytest.raises(ValueError):
        calculate_levels(entry=100, stop=100, rr=2)
    with pytest.raises(ValueError):
        calculate_levels(entry=100, stop=95, rr=0)
