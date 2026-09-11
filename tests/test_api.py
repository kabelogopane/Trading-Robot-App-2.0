"""Basic API and browser-shell tests for the research dashboard."""

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
    assert "09:45 MAIN ANCHOR" in response.text


def test_static_app_assets_are_available():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/manifest.json").status_code == 200
    assert client.get("/service-worker.js").status_code == 200


def test_sample_data_endpoint():
    response = client.get("/api/sample-data")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] > 0
    assert data["first_timestamp"] is not None
    assert data["last_timestamp"] is not None


def test_backtest_endpoint_returns_dashboard_payload():
    response = client.get("/api/backtest?risk_percent=1&risk_reward=2")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "trades" in data
    assert "bars" in data
    assert "settings" in data
    assert "net_r" in data["summary"]
    assert data["settings"]["risk_reward"] == 2


def test_backtest_rejects_risk_above_two_percent():
    response = client.get("/api/backtest?risk_percent=3&risk_reward=2")
    assert response.status_code == 422
