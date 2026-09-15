# Trading Robot App 2.0 — Architecture

## Purpose

This project is a research and paper-simulation application for the user's 45-minute time-anchor model. It does not place real-money trades.

## Model hierarchy

1. **Time model — primary**
   - 08:45 pre-open observation
   - 09:45 main anchor
   - 10:45 post-open reaction
   - 11:45 follow-through / structure check
   - 12:45 midday observation
   - 13:45 early-afternoon observation
   - 15:45 pre-close observation

2. **45-minute framework**
   - 09:45–10:30
   - 10:30–11:15
   - 11:15–12:00
   - 12:00–12:45
   - 12:45–13:30
   - 13:30–14:15
   - 14:15–15:00
   - 15:00–15:45

3. **3-minute execution layer — supporting only**
   - observes price after the 09:45 anchor
   - checks a defined reference liquidity level
   - measures displacement
   - measures market structure
   - qualifies only when objective conditions agree

## Data flow

```text
Market / historical OHLC data
        ↓
Data loader / provider adapter
        ↓
New York time normalization
        ↓
09:45 anchor detection
        ↓
45-minute window construction
        ↓
Price + liquidity measurements
        ↓
3-minute confirmation layer
        ↓
Hypothetical entry / invalidation / target
        ↓
Bar-by-bar paper backtest
        ↓
R-multiple performance + journal
        ↓
Research dashboard
```

## Important rule

ICT/SMC concepts such as liquidity, displacement, market structure, FVGs and order blocks are measurements that support the time model. They must not replace the time model or create an entry on their own.

## Safety boundary

There are no broker order-placement endpoints in this application. Any future market-data connection must remain read-only unless the project requirements are explicitly changed and separately reviewed.
