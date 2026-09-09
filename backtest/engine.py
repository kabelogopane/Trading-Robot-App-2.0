"""Bar-by-bar backtesting engine for the 45-minute time-based model.

Research/paper simulation only. This module never submits real orders.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Iterable

from strategy.displacement import measure_displacement
from strategy.entries import qualify_entry
from strategy.liquidity import detect_liquidity, swept_high, swept_low
from strategy.market_structure import classify_structure
from strategy.targets import calculate_levels, r_multiple
from strategy.time_windows import build_45m_windows, ensure_new_york, window_for_timestamp


@dataclass(frozen=True)
class BacktestConfig:
    risk_reward: float = 2.0
    displacement_multiplier: float = 1.5
    min_body_ratio: float = 0.6
    swing_lookback: int = 2
    invalidation_buffer: float = 0.0
    stop_first_on_same_bar: bool = True


@dataclass
class TradeResult:
    session_date: str
    window: str
    direction: str
    entry_time: str
    entry: float
    stop: float
    target: float
    exit_time: str | None
    exit_price: float | None
    outcome: str
    r_multiple: float | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _value(bar: Any, name: str) -> float:
    if isinstance(bar, dict):
        return float(bar[name])
    return float(getattr(bar, name))


def _timestamp(bar: Any) -> datetime:
    value = bar["timestamp"] if isinstance(bar, dict) else getattr(bar, "timestamp")
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)


def _session_date(bar: Any) -> str:
    return _timestamp(bar).date().isoformat()


def _check_exit(
    trade: dict[str, Any],
    bar: Any,
    stop_first: bool,
) -> tuple[str, float] | None:
    high = _value(bar, "high")
    low = _value(bar, "low")
    direction = trade["direction"]
    stop = trade["stop"]
    target = trade["target"]

    if direction == "bullish":
        hit_stop = low <= stop
        hit_target = high >= target
    else:
        hit_stop = high >= stop
        hit_target = low <= target

    if hit_stop and hit_target:
        if stop_first:
            return "loss", stop
        return "win", target
    if hit_stop:
        return "loss", stop
    if hit_target:
        return "win", target
    return None


def run_backtest(
    bars: Iterable[Any],
    config: BacktestConfig | None = None,
) -> list[TradeResult]:
    """Run a chronological, no-look-ahead paper backtest.

    The engine uses only bars available before the current bar to qualify a
    setup. Once a hypothetical trade is opened, later bars determine whether
    stop or target is reached. At most one trade is active at a time.
    """
    cfg = config or BacktestConfig()
    ordered = sorted(list(bars), key=_timestamp)
    if not ordered:
        return []

    results: list[TradeResult] = []
    active: dict[str, Any] | None = None
    current_session: str | None = None
    session_bars: list[Any] = []
    anchor_bars: list[Any] = []

    for bar in ordered:
        ts = _timestamp(bar)
        session = ts.date().isoformat()

        if current_session != session:
            if active is not None:
                results.append(
                    _close_at_last_bar(active, ordered, results, reason="session_end")
                )
                active = None
            current_session = session
            session_bars = []
            anchor_bars = []

        # Manage an already-open hypothetical trade before considering a new one.
        if active is not None:
            exit_result = _check_exit(active, bar, cfg.stop_first_on_same_bar)
            if exit_result is not None and ts > active["entry_time_dt"]:
                outcome, exit_price = exit_result
                results.append(_finish_trade(active, bar, outcome, exit_price))
                active = None

        session_bars.append(bar)

        # The 09:45 anchor is the first 45-minute window. We collect bars that
        # belong to it and only qualify setups after an anchor window is complete.
        windows = build_45m_windows(ts.date())
        anchor_window = windows[0]
        if anchor_window.contains(ts):
            anchor_bars.append(bar)
            continue

        if active is not None:
            continue
        if ts < anchor_window.end:
            continue

        # Use only information through the current bar; no future bars are read.
        history = session_bars[:-1]
        if len(history) < max(cfg.swing_lookback * 2 + 1, 5):
            continue
        if not anchor_bars:
            continue

        anchor_high = max(_value(b, "high") for b in anchor_bars)
        anchor_low = min(_value(b, "low") for b in anchor_bars)

        structure = classify_structure(history, lookback=cfg.swing_lookback)
        liquidity = detect_liquidity(history)
        displacement = measure_displacement(
            bar,
            history,
            multiplier=cfg.displacement_multiplier,
            min_body_ratio=cfg.min_body_ratio,
        )

        high_swept = liquidity.prior_high is not None and swept_high(bar, liquidity.prior_high)
        low_swept = liquidity.prior_low is not None and swept_low(bar, liquidity.prior_low)

        direction = displacement.direction
        liquidity_swept = high_swept if direction == "bearish" else low_swept if direction == "bullish" else False

        signal = qualify_entry(
            direction=direction,
            structure=structure,
            displacement=displacement,
            liquidity_swept=liquidity_swept,
            current_price=_value(bar, "close"),
            anchor_high=anchor_high,
            anchor_low=anchor_low,
            invalidation_buffer=cfg.invalidation_buffer,
        )
        if not signal.qualified:
            continue

        levels = calculate_levels(signal.entry, signal.invalidation, cfg.risk_reward)
        active = {
            "session_date": session,
            "window": str(window_for_timestamp(ts)) if window_for_timestamp(ts) else "post_anchor",
            "direction": signal.direction,
            "entry_time_dt": ts,
            "entry_time": ts.isoformat(),
            "entry": levels.entry,
            "stop": levels.stop,
            "target": levels.target,
            "reason": signal.reason,
        }

    if active is not None:
        results.append(_close_at_last_bar(active, ordered, results, reason="end_of_data"))

    return results


def _finish_trade(active: dict[str, Any], bar: Any, outcome: str, exit_price: float) -> TradeResult:
    direction = active["direction"]
    r = r_multiple(direction, active["entry"], exit_price, active["stop"])
    ts = _timestamp(bar)
    return TradeResult(
        session_date=active["session_date"],
        window=active["window"],
        direction=direction,
        entry_time=active["entry_time"],
        entry=active["entry"],
        stop=active["stop"],
        target=active["target"],
        exit_time=ts.isoformat(),
        exit_price=exit_price,
        outcome=outcome,
        r_multiple=r,
        reason=active["reason"],
    )


def _close_at_last_bar(
    active: dict[str, Any],
    ordered: list[Any],
    results: list[TradeResult],
    reason: str,
) -> TradeResult:
    last = ordered[-1]
    price = _value(last, "close")
    direction = active["direction"]
    r = r_multiple(direction, active["entry"], price, active["stop"])
    return TradeResult(
        session_date=active["session_date"],
        window=active["window"],
        direction=direction,
        entry_time=active["entry_time"],
        entry=active["entry"],
        stop=active["stop"],
        target=active["target"],
        exit_time=_timestamp(last).isoformat(),
        exit_price=price,
        outcome="open_at_data_end",
        r_multiple=r,
        reason=reason,
    )
