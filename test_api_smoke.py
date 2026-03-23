from fastapi.testclient import TestClient

from backend.search_and_index.api_app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "data" in body


def test_jobs_endpoint_envelope():
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "count" in body["data"]
    assert "items" in body["data"]


def test_hybrid_search_validation():
    response = client.post("/api/v1/search/hybrid", json={"query": "test", "limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "items" in body["data"]
