"""FastAPI server for Trading Robot App 2.0.

Research/paper simulation only. No broker order endpoints are exposed.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse

from backtest.engine import BacktestConfig, run_backtest
from backtest.performance import calculate_performance
from data.loader import dataframe_to_bars, load_csv

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data" / "sample_45m_sessions.csv"

app = FastAPI(
    title="Trading Robot App 2.0",
    description="Research and paper-simulation dashboard for the 45-minute time-based model.",
    version="2.0.0",
)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css")
def style() -> FileResponse:
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def javascript() -> FileResponse:
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "research_paper_simulation"}


@app.get("/api/backtest")
def backtest(
    risk_percent: float = Query(1.0, gt=0, le=2),
    risk_reward: float = Query(2.0, gt=0, le=10),
) -> dict:
    frame = load_csv(DATA_FILE)
    bars = dataframe_to_bars(frame)
    config = BacktestConfig(risk_reward=risk_reward)
    trades = run_backtest(bars, config)
    return {
        "summary": calculate_performance(trades),
        "trades": [trade.to_dict() for trade in trades],
        "bars": bars,
        "settings": {"risk_percent": risk_percent, "risk_reward": risk_reward},
    }


@app.get("/api/sample-data")
def sample_data() -> dict:
    frame = load_csv(DATA_FILE)
    return {
        "rows": len(frame),
        "first_timestamp": frame.iloc[0]["timestamp"].isoformat() if len(frame) else None,
        "last_timestamp": frame.iloc[-1]["timestamp"].isoformat() if len(frame) else None,
    }
