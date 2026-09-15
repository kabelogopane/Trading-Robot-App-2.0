"""API smoke tests for the research dashboard."""
from fastapi.testclient import TestClient
from app.server import app

client = TestClient(app)

def test_health_endpoint():
    response=client.get("/api/health")
    assert response.status_code==200
    assert response.json()["status"]=="ok"
    assert response.json()["mode"]=="research_paper_simulation"

def test_home_and_assets_are_available():
    assert client.get("/").status_code==200
    assert "Trading Robot App 2.0" in client.get("/").text
    assert client.get("/style.css").status_code==200
    assert client.get("/app.js").status_code==200
    assert client.get("/manifest.json").status_code==200
    assert client.get("/service-worker.js").status_code==200

def test_sample_data_is_3m_us500():
    data=client.get("/api/sample-data").json()
    assert data["rows"]>20
    assert data["timeframe"]=="3m"
    assert data["instrument"]=="US500.F"

def test_backtest_endpoint_returns_results_shape():
    response=client.get("/api/backtest?risk_percent=1&risk_reward=2")
    assert response.status_code==200
    data=response.json()
    assert "summary" in data and "trades" in data and "bars" in data
    assert data["settings"]["execution_timeframe"]=="3m"

def test_execution_state_endpoint():
    response=client.get("/api/execution-state")
    assert response.status_code==200
    data=response.json()
    assert data["anchor"]=="09:45 MAIN"
    assert data["execution_timeframe"]=="3m"
    assert data["reference_high"]>data["reference_low"]

def test_historical_data_endpoint():
    response=client.get("/api/historical-data")
    assert response.status_code==200
    data=response.json()
    assert data["status"]=="ready"
    assert data["timezone"]=="America/New_York"
    assert data["model_hours"]=="08:45-15:45"
    assert data["total"]["rows"]>20
    assert data["model_period"]["rows"]>0
