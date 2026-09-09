"""Provider-neutral real-time market-data interface.

This module is deliberately data-only. It does not contain order execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator


@dataclass(frozen=True)
class MarketBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class RealtimeFeed:
    """Small adapter around a caller-supplied market-data provider."""

    def __init__(self, provider: Callable[..., Any]):
        self.provider = provider

    def stream(self, symbol: str, timeframe: str = "3Min") -> Iterator[MarketBar]:
        """Yield normalized bars from the configured provider.

        Providers may return dictionaries or MarketBar objects. The provider
        itself is injected so the strategy is not tied to one broker/API.
        """
        raw_stream = self.provider(symbol=symbol, timeframe=timeframe)
        for raw in raw_stream:
            if isinstance(raw, MarketBar):
                yield raw
                continue
            yield MarketBar(
                timestamp=raw["timestamp"],
                open=float(raw["open"]),
                high=float(raw["high"]),
                low=float(raw["low"]),
                close=float(raw["close"]),
                volume=(float(raw["volume"]) if raw.get("volume") is not None else None),
            )


def alpaca_placeholder_provider(**_: Any) -> Iterator[dict[str, Any]]:
    """Placeholder for an Alpaca-compatible implementation.

    Authentication and network calls are intentionally not included yet.
    Replace this provider with a paper-data adapter when the data layer is
    connected. No trading endpoint should be added here.
    """
    raise NotImplementedError(
        "Connect a read-only/paper market-data provider before streaming live data."
    )
