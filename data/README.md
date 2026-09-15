# Data folder

The data files in this folder are research/sample inputs only.

## Important naming note

`sample_45m_sessions.csv` contains intraday bars used to build the 45-minute windows. The file is not itself a set of single 45-minute OHLC candles. The 45-minute structure is constructed by the strategy layer from the underlying bars.

`sample_3m_us500.csv` is the lower-timeframe sample used by the 3-minute execution layer.

## Expected OHLC schema

Each CSV should provide:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- optional `volume`

Timestamps are normalized by the loader before strategy calculations.

## Research boundary

Sample data is not a live market feed and must not be interpreted as live pricing or a trading recommendation.
