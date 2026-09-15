"""Read-only public web market-data adapter for paper research.

The public source is Yahoo Finance's S&P 500 index series (symbol ^GSPC).
It is a proxy for a US500 CFD, not the user's broker feed. No orders or
account data are accessed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

YAHOO_SYMBOL = "^GSPC"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_public_3m_data(period: str = "7d") -> pd.DataFrame:
    """Fetch recent public 1-minute data and resample it to 3-minute candles.

    Yahoo Finance does not reliably expose a native 3-minute interval. Using
    1-minute data and resampling keeps the robot's execution timeframe at 3m.
    The result is read-only research data and never reaches an order endpoint.
    """
    url = (
        f"{YAHOO_URL.format(symbol=quote(YAHOO_SYMBOL))}"
        f"?interval=1m&range={period}&includePrePost=true"
    )
    request = Request(url, headers={"User-Agent": "Trading-Robot-App-2.0/2.0"})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)

    chart = payload.get("chart", {})
    result = (chart.get("result") or [None])[0]
    if not result:
        error = chart.get("error") or {}
        raise RuntimeError(error.get("description") or "Public web data returned no result")

    timestamps = result.get("timestamp", [])
    quote_data = result.get("indicators", {}).get("quote", [{}])[0]
    frame = pd.DataFrame(
        {
            "timestamp": [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in timestamps],
            "open": quote_data.get("open", []),
            "high": quote_data.get("high", []),
            "low": quote_data.get("low", []),
            "close": quote_data.get("close", []),
        }
    ).dropna(subset=["timestamp", "open", "high", "low", "close"])

    if frame.empty:
        raise RuntimeError("Public web data returned no usable candles")

    frame = frame.set_index("timestamp").sort_index()
    frame.index = frame.index.tz_convert("America/New_York")
    resampled = frame.resample("3min", origin="start_day", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    )
    resampled = resampled.dropna().reset_index()
    resampled["timestamp"] = resampled["timestamp"].dt.tz_convert("UTC")
    return resampled[["timestamp", "open", "high", "low", "close"]]
