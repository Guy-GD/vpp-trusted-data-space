from fastapi.testclient import TestClient

from data_ingestion.main import app

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["service"] == "data-ingestion"
    assert body["data"]["status"] == "healthy"
