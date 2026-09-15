"""FastAPI server for Trading Robot App 2.0.

Research/paper simulation only. No broker order endpoints are exposed.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from backtest.engine import BacktestConfig, run_backtest
from backtest.performance import calculate_performance
from data.loader import dataframe_to_bars, load_csv
from strategy.execution import find_3m_confirmation
from strategy.time_windows import ensure_new_york

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR.parent / "data" / "sample_3m_us500.csv"
app = FastAPI(title="Trading Robot App 2.0", description="Research and paper-simulation dashboard for the 45-minute time-based model.", version="2.0.0")

@app.get("/")
def home(): return FileResponse(BASE_DIR / "index.html")
@app.get("/style.css")
def style(): return FileResponse(BASE_DIR / "style.css", media_type="text/css")
@app.get("/app.js")
def javascript(): return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")
@app.get("/manifest.json")
def manifest(): return FileResponse(BASE_DIR / "manifest.json", media_type="application/manifest+json")
@app.get("/service-worker.js")
def service_worker(): return FileResponse(BASE_DIR / "service-worker.js", media_type="application/javascript")
@app.get("/api/health")
def health(): return {"status":"ok", "mode":"research_paper_simulation"}

def _bars(): return dataframe_to_bars(load_csv(DATA_FILE))

def _bar_timestamp(value: datetime | str) -> datetime:
    """Return a bar timestamp as a New York-aware datetime.

    The CSV loader already converts timestamps to Python datetime objects, but
    this helper also accepts ISO strings for API/test compatibility.
    """
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_new_york(value)

@app.get("/api/backtest")
def backtest(risk_percent: float = Query(1.0, gt=0, le=2), risk_reward: float = Query(2.0, gt=0, le=10)):
    bars = _bars(); trades = run_backtest(bars, BacktestConfig(risk_reward=risk_reward, execution_timeframe="3m"))
    return {"summary":calculate_performance(trades), "trades":[t.to_dict() for t in trades], "bars":bars, "settings":{"risk_percent":risk_percent,"risk_reward":risk_reward,"execution_timeframe":"3m"}}

@app.get("/api/execution-state")
def execution_state():
    bars = _bars()
    pairs=[(b, _bar_timestamp(b["timestamp"])) for b in bars]
    pre=[b for b,ts in pairs if (ts.hour==8) or (ts.hour==9 and ts.minute<45)]
    anchor=[b for b,ts in pairs if ts.hour==9 and ts.minute==45]
    if not pre or not anchor: return {"status":"waiting","reason":"Waiting for 09:45 anchor data"}
    high=max(float(b["high"]) for b in pre); low=min(float(b["low"]) for b in pre)
    c=find_3m_confirmation(bars, reference_high=high, reference_low=low)
    return {"status":"qualified" if c.qualified else "waiting","anchor":"09:45 MAIN","reference_high":high,"reference_low":low,"execution_timeframe":"3m","direction":c.direction,"sweep_type":c.sweep_type,"confirmation_time":c.confirmation_time.isoformat() if c.confirmation_time else None,"reason":c.reason}

@app.get("/api/sample-data")
def sample_data():
    frame=load_csv(DATA_FILE)
    return {"rows":len(frame),"first_timestamp":frame.iloc[0]["timestamp"].isoformat() if len(frame) else None,"last_timestamp":frame.iloc[-1]["timestamp"].isoformat() if len(frame) else None,"timeframe":"3m","instrument":"US500.F"}
