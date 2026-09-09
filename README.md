# Trading Robot App 2.0

Research and backtesting application built around a 45-minute time-anchor trading model.

> **Important:** This project is for research and paper-simulation education. It does not guarantee profitable trading and does not place real-money trades.

## Core principle

**Time decides WHEN to analyze. Price decides WHAT to do. Liquidity decides WHERE to study the reaction.**

The 45-minute time model is the primary framework. ICT/SMC concepts are supporting measurements only and never override the time model.

## Time anchors

U.S. Eastern Time (New York): 08:45, 09:45, 10:45, 11:45, 12:45, 13:45, 15:45.

The 09:45 anchor is decomposed into consecutive 45-minute windows through 15:45. Windows use **[start, end)** boundaries, so a candle exactly on a boundary belongs to the next window.

## Technology

- Python 3.11+
- FastAPI
- Pandas / NumPy
- PyYAML
- Pydantic
- pytest
- Swappable realtime market-data adapter
- Plain HTML/CSS/JavaScript UI

## Safety boundary

This application intentionally contains **no real-money order execution**. Risk calculations are hypothetical position sizing for research only.
