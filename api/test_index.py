import json
from fastapi.testclient import TestClient
from index import app

client = TestClient(app)

def test_compute_metrics_no_filters():
    response = client.post("/", json={"regions": ["amer"]})
    assert response.status_code == 200
    data = response.json()
    assert "amer" in data
    assert "avg_latency" in data["amer"]
    assert "p95_latency" in data["amer"]
    assert "avg_uptime" in data["amer"]
    assert "breaches" in data["amer"]

def test_compute_metrics_with_service_filter():
    response = client.post("/", json={"regions": ["amer"], "services": ["support"]})
    assert response.status_code == 200
    data = response.json()
    assert "amer" in data
    # Based on the telemetry data, we can assert specific values
    assert data["amer"]["avg_latency"] == 197.15
    assert data["amer"]["p95_latency"] == 219.19
    assert data["amer"]["avg_uptime"] == 0.98
    assert data["amer"]["breaches"] == 1

def test_compute_metrics_with_multiple_services():
    response = client.post("/", json={"regions": ["amer"], "services": ["support", "checkout"]})
    assert response.status_code == 200
    data = response.json()
    assert "amer" in data
    assert data["amer"]["avg_latency"] == 182.88
    assert data["amer"]["p95_latency"] == 219.05
    assert data["amer"]["avg_uptime"] == 0.983
    assert data["amer"]["breaches"] == 2

def test_compute_metrics_empty_region():
    response = client.post("/", json={"regions": ["antarctica"]})
    assert response.status_code == 200
    data = response.json()
    assert "antarctica" in data
    assert data["antarctica"]["avg_latency"] == 0
    assert data["antarctica"]["p95_latency"] == 0
    assert data["antarctica"]["avg_uptime"] == 0
    assert data["antarctica"]["breaches"] == 0

def test_compute_metrics_no_regions():
    response = client.post("/", json={})
    assert response.status_code == 200
    data = response.json()
    assert data == {}