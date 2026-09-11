"""Bar-by-bar backtesting engine for the 45-minute + 3-minute model.

Research/paper simulation only. This module never submits real orders.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, time
from typing import Any, Iterable

from strategy.execution import find_3m_confirmation
from strategy.targets import calculate_levels, r_multiple
from strategy.time_windows import ensure_new_york, window_for_timestamp


@dataclass(frozen=True)
class BacktestConfig:
    risk_reward: float = 2.0
    displacement_multiplier: float = 1.5
    min_body_ratio: float = 0.6
    swing_lookback: int = 2
    invalidation_buffer: float = 0.0
    stop_first_on_same_bar: bool = True
    execution_timeframe: str = "3m"
    pre_anchor_start: time = time(8, 45)
    anchor_time: time = time(9, 45)


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
    return float(bar[name] if isinstance(bar, dict) else getattr(bar, name))


def _timestamp(bar: Any) -> datetime:
    value = bar["timestamp"] if isinstance(bar, dict) else getattr(bar, "timestamp")
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)


def _check_exit(trade: dict[str, Any], bar: Any, stop_first: bool) -> tuple[str, float] | None:
    high = _value(bar, "high")
    low = _value(bar, "low")
    if trade["direction"] == "bullish":
        hit_stop, hit_target = low <= trade["stop"], high >= trade["target"]
    else:
        hit_stop, hit_target = high >= trade["stop"], low <= trade["target"]
    if hit_stop and hit_target:
        return ("loss", trade["stop"]) if stop_first else ("win", trade["target"])
    if hit_stop:
        return "loss", trade["stop"]
    if hit_target:
        return "win", trade["target"]
    return None


def run_backtest(bars: Iterable[Any], config: BacktestConfig | None = None) -> list[TradeResult]:
    """Run a chronological no-look-ahead paper backtest.

    The 45-minute time model controls when the setup is evaluated. The 3-minute
    layer supplies confirmation. ICT/SMC measurements never create a trade by
    themselves. No broker or order-execution API is called.
    """
    cfg = config or BacktestConfig()
    ordered = sorted(list(bars), key=_timestamp)
    if not ordered:
        return []

    results: list[TradeResult] = []
    active: dict[str, Any] | None = None
    current_session: str | None = None
    session_bars: list[Any] = []
    last_session_bar: Any | None = None

    for bar in ordered:
        ts = _timestamp(bar)
        session = ts.date().isoformat()

        if current_session != session:
            if active is not None and last_session_bar is not None:
                results.append(_close_at_bar(active, last_session_bar, "session_end"))
            active = None
            current_session = session
            session_bars = []
            last_session_bar = None

        if active is not None:
            exit_result = _check_exit(active, bar, cfg.stop_first_on_same_bar)
            if exit_result is not None and ts > active["entry_time_dt"]:
                outcome, exit_price = exit_result
                results.append(_finish_trade(active, bar, outcome, exit_price))
                active = None

        session_bars.append(bar)
        last_session_bar = bar

        # The model needs a 08:45→09:45 reference range before the 09:45 main anchor.
        setup_bars = [
            b for b in session_bars
            if cfg.pre_anchor_start <= _timestamp(b).time() < cfg.anchor_time
        ]
        if active is not None or ts.time() <= cfg.anchor_time or len(setup_bars) < 2:
            continue

        # Evaluate only data through the current 3-minute bar.
        confirmation = find_3m_confirmation(
            session_bars,
            anchor_time=cfg.anchor_time,
            reference_high=max(_value(b, "high") for b in setup_bars),
            reference_low=min(_value(b, "low") for b in setup_bars),
            lookback=cfg.swing_lookback,
            displacement_multiplier=cfg.displacement_multiplier,
            min_body_ratio=cfg.min_body_ratio,
        )
        if not confirmation.qualified:
            continue

        # Do not open a historical trade using a confirmation that occurs later
        # than the current bar. This preserves strict bar-by-bar causality.
        if confirmation.confirmation_time is None or confirmation.confirmation_time > ts:
            continue

        entry_bar = next(
            b for b in reversed(session_bars)
            if _timestamp(b) == confirmation.confirmation_time
        )
        entry = _value(entry_bar, "close")
        setup_high = max(_value(b, "high") for b in setup_bars)
        setup_low = min(_value(b, "low") for b in setup_bars)
        stop = setup_low - cfg.invalidation_buffer if confirmation.direction == "bullish" else setup_high + cfg.invalidation_buffer

        if (confirmation.direction == "bullish" and stop >= entry) or (confirmation.direction == "bearish" and stop <= entry):
            continue

        levels = calculate_levels(entry, stop, cfg.risk_reward)
        window = window_for_timestamp(confirmation.confirmation_time)
        active = {
            "session_date": session,
            "window": window.label if window else "post_anchor",
            "direction": confirmation.direction,
            "entry_time_dt": confirmation.confirmation_time,
            "entry_time": confirmation.confirmation_time.isoformat(),
            "entry": levels.entry,
            "stop": levels.stop,
            "target": levels.target,
            "reason": confirmation.reason,
        }

    if active is not None and last_session_bar is not None:
        results.append(_close_at_bar(active, last_session_bar, "end_of_data"))
    return results


def _finish_trade(active: dict[str, Any], bar: Any, outcome: str, exit_price: float) -> TradeResult:
    ts = _timestamp(bar)
    return TradeResult(
        session_date=active["session_date"], window=active["window"], direction=active["direction"],
        entry_time=active["entry_time"], entry=active["entry"], stop=active["stop"], target=active["target"],
        exit_time=ts.isoformat(), exit_price=exit_price, outcome=outcome,
        r_multiple=r_multiple(active["direction"], active["entry"], exit_price, active["stop"]),
        reason=active["reason"],
    )


def _close_at_bar(active: dict[str, Any], bar: Any, reason: str) -> TradeResult:
    price = _value(bar, "close")
    ts = _timestamp(bar)
    return TradeResult(
        session_date=active["session_date"], window=active["window"], direction=active["direction"],
        entry_time=active["entry_time"], entry=active["entry"], stop=active["stop"], target=active["target"],
        exit_time=ts.isoformat(), exit_price=price, outcome="open_at_data_end",
        r_multiple=r_multiple(active["direction"], active["entry"], price, active["stop"]), reason=reason,
    )
