"""Basic API tests for the research dashboard."""

from fastapi.testclient import TestClient

from app.server import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "research_paper_simulation"


def test_home_page_is_available():
    response = client.get("/")
    assert response.status_code == 200
    assert "Trading Robot App 2.0" in response.text


def test_sample_data_endpoint():
    response = client.get("/api/sample-data")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] > 0
    assert data["first_timestamp"] is not None
    assert data["last_timestamp"] is not None


def test_backtest_endpoint_returns_summary_and_trades():
    response = client.get("/api/backtest")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "trades" in data
    assert "net_r" in data["summary"]
