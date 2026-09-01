from fastapi.testclient import TestClient

from api_gateway.main import app


def test_business_not_found():
    client = TestClient(app)

    response = client.get("/api/v1/demo/status/not_exists")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == 40402
    assert body["traceId"].startswith("trace_")