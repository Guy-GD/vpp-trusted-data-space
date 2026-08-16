from fastapi.testclient import TestClient
from privacy_compute.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "code" in body and isinstance(body["code"], int)
    assert "data" in body and body["data"]["service"] == "privacy-compute"
    assert "traceId" in body