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


def fetch_public_3m_data(period: str = "30d") -> pd.DataFrame:
    """Fetch recent 3-minute S&P 500 candles from a public web endpoint."""
    url = f"{YAHOO_URL.format(symbol=quote(YAHOO_SYMBOL))}?interval=3m&range={period}&includePrePost=true"
    request = Request(url, headers={"User-Agent": "Trading-Robot-App-2.0/2.0"})
    with urlopen(request, timeout=15) as response:
        payload = json.load(response)

    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    quote_data = result["indicators"]["quote"][0]
    frame = pd.DataFrame(
        {
            "timestamp": [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in timestamps],
            "open": quote_data.get("open", []),
            "high": quote_data.get("high", []),
            "low": quote_data.get("low", []),
            "close": quote_data.get("close", []),
        }
    )
    frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"]).reset_index(drop=True)
    return frame
