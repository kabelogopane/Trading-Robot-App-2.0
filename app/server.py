"""FastAPI server for Trading Robot App 2.0.

Research/paper simulation only. No broker order endpoints are exposed.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backtest.engine import BacktestConfig, run_backtest
from backtest.performance import calculate_performance
from data.historical import filter_model_hours, load_historical_csv, summarize_historical_data
from data.loader import dataframe_to_bars, load_csv
from data.quality import assess_quality
from strategy.execution import find_3m_confirmation
from strategy.targets import calculate_levels
from strategy.time_windows import ensure_new_york

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_FILE = DATA_DIR / "sample_3m_us500.csv"
HISTORICAL_FILE = DATA_DIR / "historical" / "us500_mt5.csv"

app = FastAPI(
    title="Trading Robot App 2.0",
    description="Research and paper-simulation dashboard for the 45-minute time-based model.",
    version="2.0.0",
)

allowed_origins = [
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:3000", "http://127.0.0.1:3000",
]
frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/")
if frontend_origin:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css")
def style():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def javascript():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


@app.get("/manifest.json")
def manifest():
    return FileResponse(BASE_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/service-worker.js")
def service_worker():
    return FileResponse(BASE_DIR / "service-worker.js", media_type="application/javascript")


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "research_paper_simulation"}


def _dataset_path(dataset: str) -> Path:
    normalized = dataset.lower()
    if normalized == "sample":
        return DATA_FILE
    if normalized == "historical":
        return HISTORICAL_FILE
    raise ValueError("dataset must be 'sample' or 'historical'")


def _bars(dataset: str = "sample"):
    path = _dataset_path(dataset)
    if not path.exists():
        raise FileNotFoundError(f"Dataset is not available: {path.name}")
    return dataframe_to_bars(load_csv(path))


def _bar_timestamp(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)


@app.get("/api/datasets")
def datasets():
    """List research datasets available to the dashboard."""
    return {
        "datasets": [
            {"id": "sample", "name": "Repository sample", "available": DATA_FILE.exists()},
            {"id": "historical", "name": "MT5 US500 history", "available": HISTORICAL_FILE.exists()},
        ]
    }


@app.get("/api/data-quality")
def data_quality(dataset: str = Query("sample")):
    """Return quality checks before historical data is used for research."""
    path = _dataset_path(dataset)
    if not path.exists():
        return {"dataset": dataset, "status": "unavailable", "reason": f"Missing {path.name}"}
    frame = load_csv(path)
    report = assess_quality(frame, expected_timeframe_minutes=3)
    return {"dataset": dataset, "status": "passed" if report.passed else "review", "report": report.__dict__}


@app.get("/api/backtest")
def backtest(
    risk_percent: float = Query(1.0, gt=0, le=2),
    risk_reward: float = Query(2.0, gt=0, le=10),
    dataset: str = Query("sample"),
):
    bars = _bars(dataset)
    trades = run_backtest(bars, BacktestConfig(risk_reward=risk_reward, execution_timeframe="3m"))
    return {
        "summary": calculate_performance(trades),
        "trades": [t.to_dict() for t in trades],
        "bars": bars,
        "settings": {"risk_percent": risk_percent, "risk_reward": risk_reward, "execution_timeframe": "3m", "dataset": dataset},
    }


@app.get("/api/execution-state")
def execution_state(risk_reward: float = Query(2.0, gt=0, le=10), dataset: str = Query("sample")):
    bars = _bars(dataset)
    pairs = [(b, _bar_timestamp(b["timestamp"])) for b in bars]
    pre = [b for b, ts in pairs if (ts.hour == 8) or (ts.hour == 9 and ts.minute < 45)]
    anchor = [b for b, ts in pairs if ts.hour == 9 and ts.minute == 45]
    if not pre or not anchor:
        return {"status": "waiting", "reason": "Waiting for 09:45 anchor data", "dataset": dataset}

    high = max(float(b["high"]) for b in pre)
    low = min(float(b["low"]) for b in pre)
    confirmation = find_3m_confirmation(bars, reference_high=high, reference_low=low)
    entry = invalidation = target = risk_per_unit = None
    if confirmation.qualified and confirmation.confirmation_time is not None:
        entry_bar = next((b for b in bars if _bar_timestamp(b["timestamp"]) == confirmation.confirmation_time), None)
        if entry_bar is not None:
            entry = float(entry_bar["close"])
            invalidation = low if confirmation.direction == "bullish" else high
            levels = calculate_levels(entry, invalidation, risk_reward)
            entry, invalidation, target, risk_per_unit = levels.entry, levels.stop, levels.target, levels.risk_per_unit

    return {
        "status": "qualified" if confirmation.qualified else "waiting", "dataset": dataset,
        "anchor": "09:45 MAIN", "reference_high": high, "reference_low": low,
        "execution_timeframe": "3m", "direction": confirmation.direction,
        "sweep_type": confirmation.sweep_type,
        "confirmation_time": confirmation.confirmation_time.isoformat() if confirmation.confirmation_time else None,
        "entry": entry, "invalidation": invalidation, "target": target,
        "risk_per_unit": risk_per_unit, "risk_reward": risk_reward,
        "displacement": confirmation.displacement.relative_strength if confirmation.displacement else None,
        "structure": confirmation.structure.classification if confirmation.structure else None,
        "reason": confirmation.reason,
    }


@app.get("/api/historical-data")
def historical_data():
    """Return metadata for the historical dataset used by the research engine."""
    frame = load_historical_csv(DATA_FILE)
    model_frame = filter_model_hours(frame)
    summary = summarize_historical_data(frame)
    model_summary = summarize_historical_data(model_frame)
    return {
        "status": "ready" if not frame.empty else "empty", "instrument": "US500.F",
        "timezone": "America/New_York", "source": "repository_sample_csv", "model_hours": "08:45-15:45",
        "total": summary.__dict__, "model_period": model_summary.__dict__,
    }


@app.get("/api/sample-data")
def sample_data():
    frame = load_csv(DATA_FILE)
    return {
        "rows": len(frame),
        "first_timestamp": frame.iloc[0]["timestamp"].isoformat() if len(frame) else None,
        "last_timestamp": frame.iloc[-1]["timestamp"].isoformat() if len(frame) else None,
        "timeframe": "3m", "instrument": "US500.F",
    }
