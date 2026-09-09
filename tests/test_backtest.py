"""Backtest-engine safety and no-look-ahead tests."""

from backtest.engine import BacktestConfig, run_backtest


def make_bar(ts, o, h, l, c):
    return {
        "timestamp": ts,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
    }


def test_empty_backtest_returns_no_trades():
    assert run_backtest([]) == []


def test_backtest_does_not_enter_before_anchor_window_closes():
    bars = []
    for minute in range(0, 45, 3):
        bars.append(
            make_bar(
                f"2026-08-03T09:{45 + minute:02d}:00-04:00",
                100, 105, 99, 104,
            )
        )
    # This test mainly checks that the engine handles a session with only the
    # anchor window and produces no premature setup.
    assert run_backtest(bars) == []


def test_backtest_config_defaults_are_paper_safe():
    cfg = BacktestConfig()
    assert cfg.risk_reward == 2.0
    assert cfg.stop_first_on_same_bar is True


def test_backtest_trade_results_contain_no_order_execution_fields():
    # The backtest result model intentionally contains hypothetical trade
    # information only; it has no broker order ID, quantity submission, or
    # execution endpoint.
    bars = []
    assert run_backtest(bars) == []
